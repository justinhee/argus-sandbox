"""Sales reporting: revenue by day and by category over a date range."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from shop.models import Order, OrderStatus
from shop.money import quantize

REVENUE_STATUSES = {OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED}


@dataclass
class DailyRevenue:
    day: date
    orders: int
    revenue: Decimal


def _in_range(order: Order, start: date, end: date) -> bool:
    """Inclusive of both start and end."""
    day = order.created_at.date()
    return start <= day < end


def revenue_by_day(orders: list[Order], start: date, end: date) -> list[DailyRevenue]:
    if end < start:
        raise ValueError("end must not be before start.")
    buckets: dict[date, list[Order]] = defaultdict(list)
    for order in orders:
        if order.status in REVENUE_STATUSES and _in_range(order, start, end):
            buckets[order.created_at.date()].append(order)
    result = []
    day = start
    while day <= end:
        day_orders = buckets.get(day, [])
        revenue = sum((o.total for o in day_orders), Decimal("0.00"))
        result.append(DailyRevenue(day=day, orders=len(day_orders), revenue=quantize(revenue)))
        day += timedelta(days=1)
    return result


def revenue_by_category(orders: list[Order], categories: dict[str, str]) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for order in orders:
        if order.status not in REVENUE_STATUSES:
            continue
        for line in order.lines:
            totals[categories.get(line.sku, "uncategorized")] += line.total
    return {k: quantize(v) for k, v in sorted(totals.items())}


def average_order_value(orders: list[Order]) -> Decimal:
    paid = [o for o in orders if o.status in REVENUE_STATUSES]
    if not paid:
        return Decimal("0.00")
    return quantize(sum((o.total for o in paid), Decimal("0.00")) / len(paid))


def summarize(orders: list[Order], start: date, end: date, categories: dict[str, str]) -> dict:
    days = revenue_by_day(orders, start, end)
    return {
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_revenue": str(sum((d.revenue for d in days), Decimal("0.00"))),
        "total_orders": sum(d.orders for d in days),
        "average_order_value": str(average_order_value(orders)),
        "by_category": {k: str(v) for k, v in revenue_by_category(orders, categories).items()},
        "by_day": [{"day": d.day.isoformat(), "orders": d.orders, "revenue": str(d.revenue)} for d in days],
    }
