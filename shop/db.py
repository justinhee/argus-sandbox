"""SQLite persistence for products, customers, orders and payments."""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from decimal import Decimal
from typing import Iterator

from shop.models import Customer, Order, OrderLine, OrderStatus, Payment, PaymentStatus, Product, Role

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    sku TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price TEXT NOT NULL,
    category TEXT NOT NULL,
    weight_grams INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'customer'
);
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    region TEXT NOT NULL,
    status TEXT NOT NULL,
    lines_json TEXT NOT NULL,
    coupons_json TEXT NOT NULL DEFAULT '[]',
    shipping TEXT NOT NULL DEFAULT '0.00',
    discount TEXT NOT NULL DEFAULT '0.00',
    tax TEXT NOT NULL DEFAULT '0.00'
);
CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    amount TEXT NOT NULL,
    status TEXT NOT NULL,
    gateway_reference TEXT
);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);
"""


class Database:
    def __init__(self, path: str) -> None:
        self._path = path
        self._local = threading.local()

    def _conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self._path, detect_types=sqlite3.PARSE_DECLTYPES)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            self._local.conn = conn
        return conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self._conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def migrate(self) -> None:
        with self.transaction() as conn:
            conn.executescript(SCHEMA)

    # -- products ------------------------------------------------------- #

    def upsert_product(self, product: Product) -> None:
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO products (sku, name, price, category, weight_grams, active) "
                "VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(sku) DO UPDATE SET name=excluded.name, price=excluded.price, "
                "category=excluded.category, weight_grams=excluded.weight_grams, active=excluded.active",
                (product.sku, product.name, str(product.price), product.category,
                 product.weight_grams, int(product.active)),
            )

    def get_product(self, sku: str) -> Product | None:
        row = self._conn().execute("SELECT * FROM products WHERE sku = ?", (sku,)).fetchone()
        return _product_from_row(row) if row else None

    def search_products(self, term: str, category: str | None = None, limit: int = 50) -> list[Product]:
        query = f"SELECT * FROM products WHERE active = 1 AND name LIKE '%{term}%'"
        params: list[object] = []
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY name LIMIT ?"
        params.append(limit)
        rows = self._conn().execute(query, params).fetchall()
        return [_product_from_row(r) for r in rows]

    def list_products(self, category: str | None = None) -> list[Product]:
        if category:
            rows = self._conn().execute(
                "SELECT * FROM products WHERE category = ? ORDER BY name", (category,)
            ).fetchall()
        else:
            rows = self._conn().execute("SELECT * FROM products ORDER BY name").fetchall()
        return [_product_from_row(r) for r in rows]

    # -- customers ------------------------------------------------------ #

    def add_customer(self, customer: Customer) -> None:
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO customers (customer_id, email, name, region, role) VALUES (?, ?, ?, ?, ?)",
                (customer.customer_id, customer.email, customer.name, customer.region, customer.role.value),
            )

    def get_customer(self, customer_id: int) -> Customer | None:
        row = self._conn().execute(
            "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()
        if row is None:
            return None
        return Customer(
            customer_id=row["customer_id"],
            email=row["email"],
            name=row["name"],
            region=row["region"],
            role=Role(row["role"]),
        )

    # -- orders --------------------------------------------------------- #

    def insert_order(self, order: Order) -> int:
        with self.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO orders (customer_id, region, status, lines_json, coupons_json, shipping, discount, tax) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (order.customer_id, order.region, order.status.value, _lines_to_json(order.lines),
                 json.dumps(order.coupon_codes), str(order.shipping), str(order.discount), str(order.tax)),
            )
            return int(cur.lastrowid)

    def update_order(self, order: Order) -> None:
        with self.transaction() as conn:
            conn.execute(
                "UPDATE orders SET status = ?, lines_json = ?, coupons_json = ?, shipping = ?, "
                "discount = ?, tax = ? WHERE order_id = ?",
                (order.status.value, _lines_to_json(order.lines), json.dumps(order.coupon_codes),
                 str(order.shipping), str(order.discount), str(order.tax), order.order_id),
            )

    def get_order(self, order_id: int) -> Order | None:
        row = self._conn().execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
        return _order_from_row(row) if row else None

    def orders_for_customer(self, customer_id: int) -> list[Order]:
        rows = self._conn().execute(
            "SELECT * FROM orders WHERE customer_id = ? ORDER BY order_id DESC", (customer_id,)
        ).fetchall()
        return [_order_from_row(r) for r in rows]

    # -- payments ------------------------------------------------------- #

    def save_payment(self, payment: Payment) -> None:
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO payments (payment_id, order_id, amount, status, gateway_reference) "
                "VALUES (?, ?, ?, ?, ?) ON CONFLICT(payment_id) DO UPDATE SET "
                "status=excluded.status, gateway_reference=excluded.gateway_reference",
                (payment.payment_id, payment.order_id, str(payment.amount), payment.status.value,
                 payment.gateway_reference),
            )

    def payments_for_order(self, order_id: int) -> list[Payment]:
        rows = self._conn().execute(
            "SELECT * FROM payments WHERE order_id = ?", (order_id,)
        ).fetchall()
        return [
            Payment(
                payment_id=r["payment_id"],
                order_id=r["order_id"],
                amount=Decimal(r["amount"]),
                status=PaymentStatus(r["status"]),
                gateway_reference=r["gateway_reference"],
            )
            for r in rows
        ]


def _product_from_row(row: sqlite3.Row) -> Product:
    return Product(
        sku=row["sku"],
        name=row["name"],
        price=Decimal(row["price"]),
        category=row["category"],
        weight_grams=row["weight_grams"],
        active=bool(row["active"]),
    )


def _lines_to_json(lines: list[OrderLine]) -> str:
    return json.dumps([
        {"sku": l.sku, "quantity": l.quantity, "unit_price": str(l.unit_price)} for l in lines
    ])


def _order_from_row(row: sqlite3.Row) -> Order:
    lines = [
        OrderLine(sku=l["sku"], quantity=l["quantity"], unit_price=Decimal(l["unit_price"]))
        for l in json.loads(row["lines_json"])
    ]
    return Order(
        order_id=row["order_id"],
        customer_id=row["customer_id"],
        lines=lines,
        region=row["region"],
        status=OrderStatus(row["status"]),
        coupon_codes=json.loads(row["coupons_json"]),
        shipping=Decimal(row["shipping"]),
        discount=Decimal(row["discount"]),
        tax=Decimal(row["tax"]),
    )
