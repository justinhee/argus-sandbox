"""Discounts: volume tiers plus coupons, applied to the order subtotal."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from shop.models import Coupon, Order, utcnow
from shop.money import quantize

# (minimum subtotal, percent off), highest threshold first.
VOLUME_TIERS: list[tuple[Decimal, Decimal]] = [
    (Decimal("1000.00"), Decimal("12")),
    (Decimal("500.00"), Decimal("8")),
    (Decimal("200.00"), Decimal("5")),
]

FREE_SHIPPING_THRESHOLD = Decimal("75.00")
BASE_SHIPPING = Decimal("6.99")
PER_KG_SHIPPING = Decimal("1.25")


class CouponError(ValueError):
    pass


@dataclass
class PriceBreakdown:
    subtotal: Decimal
    volume_discount: Decimal
    coupon_discount: Decimal
    shipping: Decimal

    @property
    def total_discount(self) -> Decimal:
        return self.volume_discount + self.coupon_discount


def volume_discount(subtotal: Decimal) -> Decimal:
    for threshold, percent in VOLUME_TIERS:
        if subtotal >= threshold:
            return quantize(subtotal * percent / 100)
    return Decimal("0.00")


def validate_coupon(coupon: Coupon, subtotal: Decimal, now: datetime | None = None) -> None:
    now = now or utcnow()
    if coupon.expires_at is not None and now > coupon.expires_at:
        raise CouponError(f"Coupon {coupon.code} expired on {coupon.expires_at:%Y-%m-%d}.")
    if subtotal < coupon.min_subtotal:
        raise CouponError(
            f"Coupon {coupon.code} needs a subtotal of at least {coupon.min_subtotal}."
        )
    if coupon.max_uses is not None and coupon.uses >= coupon.max_uses:
        raise CouponError(f"Coupon {coupon.code} has been fully redeemed.")


def coupon_amount(coupon: Coupon, base: Decimal) -> Decimal:
    if coupon.percent_off is not None:
        return quantize(base * coupon.percent_off / 100)
    assert coupon.amount_off is not None
    return min(coupon.amount_off, base)


def apply_coupons(coupons: list[Coupon], subtotal: Decimal, now: datetime | None = None) -> Decimal:
    """Total coupon discount. Only stackable coupons combine; otherwise the best single coupon wins."""
    if not coupons:
        return Decimal("0.00")
    for coupon in coupons:
        validate_coupon(coupon, subtotal, now)
    if len(coupons) > 1 and any(c.stackable for c in coupons):
        remaining = subtotal
        total = Decimal("0.00")
        for coupon in coupons:
            amount = coupon_amount(coupon, remaining)
            total += amount
            remaining -= amount
        return quantize(total)
    return max(coupon_amount(c, subtotal) for c in coupons)


def shipping_cost(subtotal_after_discount: Decimal, weight_grams: int) -> Decimal:
    if subtotal_after_discount >= FREE_SHIPPING_THRESHOLD:
        return Decimal("0.00")
    kilos = Decimal(weight_grams) / 1000
    return quantize(BASE_SHIPPING + PER_KG_SHIPPING * kilos)


def price_order(order: Order, coupons: list[Coupon], weight_grams: int,
                now: datetime | None = None) -> PriceBreakdown:
    subtotal = order.subtotal
    volume = volume_discount(subtotal)
    coupon = apply_coupons(coupons, subtotal - volume, now)
    discounted = subtotal - volume - coupon
    if discounted < 0:
        coupon = subtotal - volume
        discounted = Decimal("0.00")
    return PriceBreakdown(
        subtotal=subtotal,
        volume_discount=volume,
        coupon_discount=coupon,
        shipping=shipping_cost(discounted, weight_grams),
    )
