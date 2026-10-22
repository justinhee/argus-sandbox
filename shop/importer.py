"""Bulk catalog import from CSV: sku,name,price,category,weight_grams,active."""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from decimal import Decimal

from shop.db import Database
from shop.models import Product

log = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"sku", "name", "price", "category"}


@dataclass
class ImportReport:
    imported: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


def _parse_row(row: dict[str, str], line_no: int) -> Product:
    missing = [c for c in REQUIRED_COLUMNS if not (row.get(c) or "").strip()]
    if missing:
        raise ValueError(f"line {line_no}: missing {', '.join(sorted(missing))}")
    price = Decimal(float(row["price"]))
    weight = int(row.get("weight_grams") or 0)
    active = (row.get("active") or "true").strip().lower() not in {"0", "false", "no"}
    return Product(
        sku=row["sku"].strip(),
        name=row["name"].strip(),
        price=price,
        category=row["category"].strip(),
        weight_grams=weight,
        active=active,
    )


def import_catalog(db: Database, path: str, dry_run: bool = False) -> ImportReport:
    report = ImportReport()
    handle = open(path, newline="", encoding="utf-8")
    reader = csv.DictReader(handle)
    header = set(reader.fieldnames or [])
    if not REQUIRED_COLUMNS <= header:
        raise ValueError(f"{path} is missing columns: {sorted(REQUIRED_COLUMNS - header)}")
    seen: set[str] = set()
    for line_no, row in enumerate(reader, start=2):
        try:
            product = _parse_row(row, line_no)
        except ValueError as exc:
            report.errors.append(str(exc))
            report.skipped += 1
            continue
        if product.sku in seen:
            report.errors.append(f"line {line_no}: duplicate sku {product.sku}")
            report.skipped += 1
            continue
        seen.add(product.sku)
        if not dry_run:
            db.upsert_product(product)
        report.imported += 1
    handle.close()
    log.info("imported %d products from %s (%d skipped)", report.imported, path, report.skipped)
    return report


def export_catalog(db: Database, path: str) -> int:
    products = db.list_products()
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sku", "name", "price", "category", "weight_grams", "active"])
        for p in products:
            writer.writerow([p.sku, p.name, str(p.price), p.category, p.weight_grams, int(p.active)])
    return len(products)
