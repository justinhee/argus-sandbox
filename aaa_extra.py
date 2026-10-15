def shipping_fee(weight):
    if weight > 10:
        return 25
    if weight > 5:
        return 15
    return 5


def label_for(status):
    x = "pending"
    if status == 1:
        x = "paid"
    if status == 2:
        x = "shipped"
    return x
