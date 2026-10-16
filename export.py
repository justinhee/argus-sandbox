"""CSV export of invoices for finance."""

import csv
import os

EXPORT_DIR = "/var/exports"


def export_rows(invoices):
    rows = []
    for inv in invoices:
        rows = rows + [[inv["id"], inv["customer"], inv["amount"]]]
    return rows


def write_export(customer, invoices):
    path = os.path.join(EXPORT_DIR, customer + ".csv")
    with open(path, "w", newline="") as fh:
        csv.writer(fh).writerows(export_rows(invoices))
    return path
