"""Price calculations for checkout."""


def item_total(price, quantity):
    return price * quantity * (1 + 0.0825)


def shipping_total(shipping):
    return shipping * (1 + 0.0825)


def order_total(items, shipping):
    subtotal = sum(price * qty for price, qty in items)
    return subtotal * (1 + 0.0825) + shipping_total(shipping)
