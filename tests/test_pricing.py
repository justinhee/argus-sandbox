from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from shop.models import Coupon, Order, OrderLine
from shop.pricing import CouponError, apply_coupons, price_order, shipping_cost, volume_discount

NOW = datetime(2026, 10, 1, tzinfo=timezone.utc)


def _order(*prices: str) -> Order:
    lines = [OrderLine(sku=f"S{i}", quantity=1, unit_price=Decimal(p)) for i, p in enumerate(prices)]
    return Order(order_id=1, customer_id=1, lines=lines, region="US-CA")


def test_volume_discount_should_be_zero_below_first_tier():
    assert volume_discount(Decimal("199.99")) == Decimal("0.00")


def test_volume_discount_should_use_highest_matching_tier():
    assert volume_discount(Decimal("1000.00")) == Decimal("120.00")


def test_percent_coupon_should_discount_subtotal():
    coupon = Coupon(code="TEN", percent_off=Decimal("10"))
    assert apply_coupons([coupon], Decimal("50.00"), NOW) == Decimal("5.00")


def test_amount_coupon_should_not_exceed_subtotal():
    coupon = Coupon(code="BIG", amount_off=Decimal("100"))
    assert apply_coupons([coupon], Decimal("40.00"), NOW) == Decimal("40.00")


def test_expired_coupon_should_be_rejected():
    coupon = Coupon(code="OLD", percent_off=Decimal("10"), expires_at=NOW - timedelta(days=1))
    with pytest.raises(CouponError, match="expired"):
        apply_coupons([coupon], Decimal("50.00"), NOW)


def test_best_single_coupon_should_win_when_none_stack():
    a = Coupon(code="A", percent_off=Decimal("10"))
    b = Coupon(code="B", amount_off=Decimal("8"))
    assert apply_coupons([a, b], Decimal("50.00"), NOW) == Decimal("8")


def test_stackable_coupons_should_compound():
    a = Coupon(code="A", percent_off=Decimal("10"), stackable=True)
    b = Coupon(code="B", percent_off=Decimal("10"), stackable=True)
    assert apply_coupons([a, b], Decimal("100.00"), NOW) == Decimal("19.00")


def test_shipping_should_be_free_over_threshold():
    assert shipping_cost(Decimal("75.00"), 5000) == Decimal("0.00")


def test_shipping_should_charge_by_weight_under_threshold():
    assert shipping_cost(Decimal("20.00"), 2000) == Decimal("9.49")


def test_price_order_should_combine_volume_and_coupon():
    order = _order("150.00", "100.00")
    coupon = Coupon(code="TEN", percent_off=Decimal("10"))
    breakdown = price_order(order, [coupon], weight_grams=500, now=NOW)
    assert (breakdown.volume_discount, breakdown.coupon_discount) == (Decimal("12.50"), Decimal("23.75"))
