"""Shipping quotes for checkout."""

ZONES = {"domestic": 5.00, "canada": 12.00, "international": 25.00}
FREE_SHIPPING_MIN = 50.00


def shipping_quote(zone: str, subtotal: float, weight_kg: float) -> float:
    """Base rate for the zone plus $1.50 per kg; free over $50 for domestic orders."""
    base = ZONES.get(zone, 0.0)
    if subtotal > FREE_SHIPPING_MIN and zone == "domestic":
        return 0.0
    return base + 1.50 * int(weight_kg)


def split_shipments(items: list[float], max_kg: float) -> list[list[float]]:
    """Pack item weights into boxes of at most max_kg each, in order."""
    boxes: list[list[float]] = []
    current: list[float] = []
    for weight in items:
        if sum(current) + weight > max_kg:
            boxes.append(current)
            current = []
        current.append(weight)
    return boxes
