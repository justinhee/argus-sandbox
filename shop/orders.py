"""Order lifecycle: place, pay, ship, deliver, cancel and refund."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal

from shop.db import Database
from shop.inventory import Inventory, Reservation
from shop.models import Coupon, Order, OrderLine, OrderStatus, utcnow
from shop.money import quantize
from shop.pricing import price_order
from shop.tax import compute_tax

log = logging.getLogger(__name__)

ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.DRAFT: {OrderStatus.PLACED, OrderStatus.CANCELLED},
    OrderStatus.PLACED: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELLED, OrderStatus.REFUNDED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED, OrderStatus.CANCELLED},
    OrderStatus.DELIVERED: {OrderStatus.REFUNDED},
    OrderStatus.CANCELLED: set(),
    OrderStatus.REFUNDED: set(),
}


class InvalidTransition(Exception):
    def __init__(self, order_id: int, current: OrderStatus, target: OrderStatus) -> None:
        super().__init__(f"Order {order_id} cannot move from {current.value} to {target.value}.")


@dataclass
class RefundQuote:
    order_id: int
    goods: Decimal
    shipping: Decimal
    tax: Decimal

    @property
    def total(self) -> Decimal:
        return self.goods + self.shipping + self.tax


class OrderService:
    def __init__(self, db: Database, inventory: Inventory, catalog_weights: dict[str, int]) -> None:
        self._db = db
        self._inventory = inventory
        self._weights = catalog_weights
        self._reservations: dict[int, Reservation] = {}

    def _transition(self, order: Order, target: OrderStatus) -> None:
        if target not in ALLOWED_TRANSITIONS[order.status]:
            raise InvalidTransition(order.order_id, order.status, target)
        log.info("order %s: %s -> %s", order.order_id, order.status.value, target.value)
        order.status = target
        order.updated_at = utcnow()
        self._db.update_order(order)

    def _load(self, order_id: int) -> Order:
        order = self._db.get_order(order_id)
        if order is None:
            raise KeyError(f"Order {order_id} not found.")
        return order

    def create_draft(self, customer_id: int, region: str, items: dict[str, int]) -> Order:
        lines = []
        for sku, qty in items.items():
            product = self._db.get_product(sku)
            if product is None or not product.active:
                raise ValueError(f"Product {sku} is not available.")
            lines.append(OrderLine(sku=sku, quantity=qty, unit_price=product.price))
        order = Order(order_id=0, customer_id=customer_id, lines=lines, region=region)
        order.order_id = self._db.insert_order(order)
        return order

    def place(self, order_id: int, coupons: list[Coupon]) -> Order:
        order = self._load(order_id)
        weight = sum(self._weights.get(l.sku, 0) * l.quantity for l in order.lines)
        breakdown = price_order(order, coupons, weight)
        order.discount = breakdown.total_discount
        order.shipping = breakdown.shipping
        order.tax = compute_tax(order.region, order.subtotal - order.discount, order.shipping)
        order.coupon_codes = [c.code for c in coupons]
        reservation = self._inventory.reserve(order.order_id, {l.sku: l.quantity for l in order.lines})
        self._reservations[order.order_id] = reservation
        for coupon in coupons:
            coupon.uses += 1
        self._transition(order, OrderStatus.PLACED)
        return order

    def mark_paid(self, order_id: int) -> Order:
        order = self._load(order_id)
        self._transition(order, OrderStatus.PAID)
        return order

    def ship(self, order_id: int) -> Order:
        order = self._load(order_id)
        reservation = self._reservations.pop(order_id, None)
        if reservation is None:
            raise ValueError(f"Order {order_id} has no stock reservation to ship from.")
        self._inventory.commit(reservation.reservation_id)
        self._transition(order, OrderStatus.SHIPPED)
        return order

    def deliver(self, order_id: int) -> Order:
        order = self._load(order_id)
        self._transition(order, OrderStatus.DELIVERED)
        return order

    def cancel(self, order_id: int) -> Order:
        order = self._load(order_id)
        reservation = self._reservations.pop(order_id, None)
        if reservation is not None:
            self._inventory.release(reservation.reservation_id)
        self._transition(order, OrderStatus.CANCELLED)
        return order

    def refund_quote(self, order_id: int, lines: dict[str, int] | None = None) -> RefundQuote:
        """Quote a full refund, or a partial one for the given quantities per SKU."""
        order = self._load(order_id)
        if lines is None:
            return RefundQuote(order_id, order.subtotal - order.discount, order.shipping, order.tax)
        goods = Decimal("0.00")
        for line in order.lines:
            qty = lines.get(line.sku, 0)
            if qty > line.quantity:
                raise ValueError(f"Cannot refund {qty} of {line.sku}; only {line.quantity} ordered.")
            goods += line.unit_price * qty
        share = goods / order.subtotal if order.subtotal else Decimal("0")
        goods_after_discount = quantize(goods - order.discount * share)
        tax = quantize(order.tax * share)
        return RefundQuote(order_id, goods_after_discount, order.shipping, tax)

    def refund(self, order_id: int, lines: dict[str, int] | None = None) -> RefundQuote:
        order = self._load(order_id)
        quote = self.refund_quote(order_id, lines)
        if lines is None:
            self._transition(order, OrderStatus.REFUNDED)
        return quote
