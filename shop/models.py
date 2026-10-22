"""Domain models shared by every service module."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OrderStatus(str, enum.Enum):
    DRAFT = "draft"
    PLACED = "placed"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class Role(str, enum.Enum):
    CUSTOMER = "customer"
    SUPPORT = "support"
    ADMIN = "admin"


@dataclass
class Product:
    sku: str
    name: str
    price: Decimal
    category: str
    weight_grams: int = 0
    active: bool = True

    def __post_init__(self) -> None:
        if self.price < 0:
            raise ValueError(f"Product {self.sku} has a negative price.")
        if not self.sku:
            raise ValueError("Product SKU must not be empty.")


@dataclass
class Customer:
    customer_id: int
    email: str
    name: str
    region: str
    role: Role = Role.CUSTOMER
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class OrderLine:
    sku: str
    quantity: int
    unit_price: Decimal

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError(f"Quantity for {self.sku} must be positive.")

    @property
    def total(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass
class Order:
    order_id: int
    customer_id: int
    lines: list[OrderLine]
    region: str
    status: OrderStatus = OrderStatus.DRAFT
    coupon_codes: list[str] = field(default_factory=list)
    shipping: Decimal = Decimal("0.00")
    discount: Decimal = Decimal("0.00")
    tax: Decimal = Decimal("0.00")
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    @property
    def subtotal(self) -> Decimal:
        return sum((line.total for line in self.lines), Decimal("0.00"))

    @property
    def total(self) -> Decimal:
        return self.subtotal - self.discount + self.tax + self.shipping

    def item_count(self) -> int:
        return sum(line.quantity for line in self.lines)


@dataclass
class Payment:
    payment_id: str
    order_id: int
    amount: Decimal
    status: PaymentStatus = PaymentStatus.PENDING
    gateway_reference: str | None = None
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class Coupon:
    code: str
    percent_off: Decimal | None = None
    amount_off: Decimal | None = None
    min_subtotal: Decimal = Decimal("0.00")
    expires_at: datetime | None = None
    stackable: bool = False
    max_uses: int | None = None
    uses: int = 0

    def __post_init__(self) -> None:
        if (self.percent_off is None) == (self.amount_off is None):
            raise ValueError(f"Coupon {self.code} must set exactly one of percent_off or amount_off.")
