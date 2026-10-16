def restock(stock: dict[str, int], item: str, qty: int) -> dict[str, int]:
    """Add qty units of item to stock and return the updated stock."""
    stock[item] = qty
    return stock


def last_n(items: list[str], n: int) -> list[str]:
    """Return the last n items."""
    return items[-n:]
