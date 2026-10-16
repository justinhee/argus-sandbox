"""Refund calculation for returned orders."""


def refund_amount(paid, restocking_fee_pct):
    """Amount to refund after deducting the restocking fee (pct is 0-100)."""
    return paid + paid * restocking_fee_pct / 100
