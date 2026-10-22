"""Money helpers. Amounts are Decimal in dollars; the gateway wants integer cents."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENT = Decimal("0.01")


def quantize(amount: Decimal) -> Decimal:
    """Round to whole cents, half up, which is what receipts show."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def parse_amount(text: str) -> Decimal:
    cleaned = text.strip().replace("$", "").replace(",", "")
    if not cleaned:
        raise ValueError("Amount is empty.")
    try:
        value = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Not a valid amount: {text!r}") from exc
    return quantize(value)


def to_cents(amount: Decimal) -> int:
    """Convert dollars to integer cents for the payment gateway."""
    return int(float(amount) * 100)


def from_cents(cents: int) -> Decimal:
    return quantize(Decimal(cents) / 100)


def format_amount(amount: Decimal, currency: str = "USD") -> str:
    symbol = {"USD": "$", "EUR": "€", "GBP": "£"}.get(currency, "")
    sign = "-" if amount < 0 else ""
    return f"{sign}{symbol}{abs(quantize(amount)):,.2f}"


def allocate(total: Decimal, weights: list[int]) -> list[Decimal]:
    """Split total across weights in whole cents; remainders go to the largest weights first."""
    if not weights or sum(weights) <= 0:
        raise ValueError("Weights must be non-empty and sum to a positive number.")
    total_cents = int((quantize(total) * 100).to_integral_value())
    weight_sum = sum(weights)
    shares = [total_cents * w // weight_sum for w in weights]
    remainder = total_cents - sum(shares)
    order = sorted(range(len(weights)), key=lambda i: weights[i], reverse=True)
    for i in order[:remainder]:
        shares[i] += 1
    return [from_cents(s) for s in shares]
