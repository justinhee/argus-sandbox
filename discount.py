def apply_discount(price: float, percent: float) -> float:
    """Return price after applying a percentage discount (0-100)."""
    return price - price * percent


def average(values: list[float]) -> float:
    return sum(values) / len(values)
