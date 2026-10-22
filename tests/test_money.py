from decimal import Decimal

import pytest

from shop.money import allocate, format_amount, from_cents, parse_amount, quantize


def test_quantize_should_round_half_up():
    assert quantize(Decimal("1.005")) == Decimal("1.01")


def test_parse_amount_should_strip_symbols_and_commas():
    assert parse_amount("$1,234.50") == Decimal("1234.50")


def test_parse_amount_should_reject_garbage():
    with pytest.raises(ValueError, match="Not a valid amount"):
        parse_amount("twelve")


def test_from_cents_should_return_dollars():
    assert from_cents(1999) == Decimal("19.99")


def test_format_amount_should_show_negative_sign_before_symbol():
    assert format_amount(Decimal("-5")) == "-$5.00"


def test_allocate_should_preserve_total():
    shares = allocate(Decimal("10.00"), [1, 1, 1])
    assert sum(shares) == Decimal("10.00")


def test_allocate_should_give_remainder_to_largest_weight():
    assert allocate(Decimal("0.05"), [3, 1]) == [Decimal("0.04"), Decimal("0.01")]
