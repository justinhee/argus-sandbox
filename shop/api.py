"""Framework-free request handlers. A web adapter maps HTTP requests onto these."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Callable

from shop.auth import AuthError, Principal, require_role, verify_token
from shop.cache import TTLCache
from shop.db import Database
from shop.models import Coupon, Role
from shop.money import format_amount
from shop.orders import InvalidTransition, OrderService
from shop.ratelimit import RateLimiter

log = logging.getLogger(__name__)


@dataclass
class Request:
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, str] = field(default_factory=dict)
    body: dict[str, Any] = field(default_factory=dict)
    client_ip: str = "0.0.0.0"


@dataclass
class Response:
    status: int
    body: dict[str, Any]


Handler = Callable[[Request, Principal], Response]


def error(status: int, message: str) -> Response:
    return Response(status, {"error": message})


class Api:
    def __init__(self, db: Database, orders: OrderService, limiter: RateLimiter,
                 coupons: dict[str, Coupon], token_secret: str, cache: TTLCache) -> None:
        self._db = db
        self._orders = orders
        self._limiter = limiter
        self._coupons = coupons
        self._secret = token_secret
        self._cache = cache
        self._routes: dict[tuple[str, str], Handler] = {
            ("GET", "/products"): self.search_products,
            ("POST", "/orders"): self.create_order,
            ("POST", "/orders/place"): self.place_order,
            ("POST", "/orders/cancel"): self.cancel_order,
            ("GET", "/orders"): self.list_orders,
            ("POST", "/admin/refund"): self.refund_order,
        }

    def handle(self, request: Request) -> Response:
        if not self._limiter.allow(request.client_ip):
            return error(429, "Too many requests.")
        handler = self._routes.get((request.method, request.path))
        if handler is None:
            return error(404, f"No route for {request.method} {request.path}.")
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return error(401, "Missing bearer token.")
        try:
            principal = verify_token(self._secret, auth.removeprefix("Bearer "))
        except AuthError as exc:
            return error(401, str(exc))
        try:
            return handler(request, principal)
        except InvalidTransition as exc:
            return error(409, str(exc))
        except (KeyError, ValueError) as exc:
            return error(400, str(exc))
        except Exception:
            log.exception("unhandled error on %s %s", request.method, request.path)
            return error(500, "Internal error.")

    # -- handlers ------------------------------------------------------- #

    def search_products(self, request: Request, principal: Principal) -> Response:
        term = request.params.get("q", "")
        category = request.params.get("category")
        key = f"search:{term}:{category}"
        cached = self._cache.get(key)
        if cached is not None:
            return Response(200, cached)
        products = self._db.search_products(term, category)
        body = {"products": [
            {"sku": p.sku, "name": p.name, "price": format_amount(p.price), "category": p.category}
            for p in products
        ]}
        self._cache.set(key, body)
        return Response(200, body)

    def create_order(self, request: Request, principal: Principal) -> Response:
        items = {str(k): int(v) for k, v in request.body.get("items", {}).items()}
        if not items:
            return error(400, "An order needs at least one item.")
        customer = self._db.get_customer(principal.customer_id)
        if customer is None:
            return error(404, "Customer not found.")
        order = self._orders.create_draft(customer.customer_id, customer.region, items)
        return Response(201, {"order_id": order.order_id, "subtotal": str(order.subtotal)})

    def place_order(self, request: Request, principal: Principal) -> Response:
        order_id = int(request.body["order_id"])
        order = self._db.get_order(order_id)
        if order is None or order.customer_id != principal.customer_id:
            return error(404, "Order not found.")
        codes = request.body.get("coupons", [])
        unknown = [c for c in codes if c not in self._coupons]
        if unknown:
            return error(400, f"Unknown coupon(s): {', '.join(unknown)}")
        placed = self._orders.place(order_id, [self._coupons[c] for c in codes])
        return Response(200, {
            "order_id": placed.order_id,
            "status": placed.status.value,
            "total": str(placed.total),
        })

    def cancel_order(self, request: Request, principal: Principal) -> Response:
        order_id = int(request.body["order_id"])
        order = self._db.get_order(order_id)
        if order is None or (order.customer_id != principal.customer_id and not principal.is_staff):
            return error(404, "Order not found.")
        cancelled = self._orders.cancel(order_id)
        return Response(200, {"order_id": cancelled.order_id, "status": cancelled.status.value})

    def list_orders(self, request: Request, principal: Principal) -> Response:
        customer_id = principal.customer_id
        if principal.is_staff and "customer_id" in request.params:
            customer_id = int(request.params["customer_id"])
        orders = self._db.orders_for_customer(customer_id)
        return Response(200, {"orders": [
            {"order_id": o.order_id, "status": o.status.value, "total": str(o.total)} for o in orders
        ]})

    def refund_order(self, request: Request, principal: Principal) -> Response:
        order_id = int(request.body["order_id"])
        lines = request.body.get("lines")
        quote = self._orders.refund(order_id, {str(k): int(v) for k, v in lines.items()} if lines else None)
        log.info("refund on order %s by %s: %s", order_id, principal.customer_id, quote.total)
        return Response(200, {
            "order_id": order_id,
            "refund_total": str(quote.total),
            "goods": str(quote.goods),
            "shipping": str(quote.shipping),
            "tax": str(quote.tax),
        })
