"""Sales tax by region. Rates are percentages."""

from __future__ import annotations

import logging
from decimal import Decimal

from shop.money import quantize

log = logging.getLogger(__name__)

TAX_RATES: dict[str, Decimal] = {
    "US-CA": Decimal("7.25"),
    "US-NY": Decimal("4.00"),
    "US-TX": Decimal("6.25"),
    "US-WA": Decimal("6.50"),
    "US-OR": Decimal("0.00"),
}

# Shipping is taxable in these regions.
TAXABLE_SHIPPING = {"US-NY", "US-TX", "US-WA"}


class UnknownRegion(KeyError):
    pass


def rate_for(region: str) -> Decimal:
    try:
        return TAX_RATES[region]
    except KeyError:
        log.warning("No tax rate configured for region %s; charging no tax.", region)
        return Decimal("0.00")


def compute_tax(region: str, taxable_goods: Decimal, shipping: Decimal) -> Decimal:
    rate = rate_for(region)
    base = taxable_goods
    if region in TAXABLE_SHIPPING:
        base += shipping
    return quantize(base * rate / 100)


def tax_breakdown(region: str, taxable_goods: Decimal, shipping: Decimal) -> dict[str, str]:
    rate = rate_for(region)
    tax = compute_tax(region, taxable_goods, shipping)
    return {
        "region": region,
        "rate_percent": str(rate),
        "taxable_goods": str(quantize(taxable_goods)),
        "shipping_taxable": str(region in TAXABLE_SHIPPING).lower(),
        "tax": str(tax),
    }
