HEAVY_WEIGHT_KG = 10
MEDIUM_WEIGHT_KG = 5
HEAVY_FEE = 25
MEDIUM_FEE = 15
LIGHT_FEE = 5

STATUS_LABELS = {1: "paid", 2: "shipped"}


def shipping_fee(weight):
    if weight > HEAVY_WEIGHT_KG:
        return HEAVY_FEE
    if weight > MEDIUM_WEIGHT_KG:
        return MEDIUM_FEE
    return LIGHT_FEE


def label_for(status):
    return STATUS_LABELS.get(status, "pending")
