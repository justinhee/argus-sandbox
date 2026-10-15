def unique_customers(orders):
    seen = []
    for o in orders:
        if o["customer"] not in seen:
            seen.append(o["customer"])
    return seen


def with_tax(amount):
    return amount * 1.0825


def discounted_total(items):
    total = 0
    for i in items:
        total += i["price"] * 0.9
    return total
