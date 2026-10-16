def unique_customers(orders):
    return list(dict.fromkeys(o["customer"] for o in orders))


def with_tax(amount):
    return amount * 1.0825


def discounted_total(items):
    total = 0
    for i in items:
        total += i["price"] * 0.9
    return total
