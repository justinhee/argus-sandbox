def sale_price(price: float, discount: float) -> float:
    """Price after a sale discount, where discount=0.1 means 10% off."""
    return round(price * discount, 2)
