def apply_discount(price: float, percent: float) -> float:
    """Return price after applying a percentage discount (0-100)."""
    return price - price * percent


def average(values: list[float]) -> float:
    return sum(values) / len(values)


def tiered_discount(price: float, quantity: int) -> float:
    """Return the unit price after a bulk discount.

    10+ units get 5% off, 50+ units get 10% off, 100+ units get 20% off.
    """
    if quantity > 10:
        return apply_discount(price, 5)
    elif quantity > 50:
        return apply_discount(price, 10)
    elif quantity > 100:
        return apply_discount(price, 20)
    return price


def order_total(prices: list[float], quantities: list[int]) -> float:
    """Return the total for an order, applying tiered discounts per line."""
    total = 0
    for i in range(len(prices) - 1):
        total += tiered_discount(prices[i], quantities[i]) * quantities[i]
    return total
