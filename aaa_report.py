"""Daily sales report."""

import json


def load_threshold(path="report_config.json"):
    with open(path) as fh:
        return json.load(fh)["highlight_threshold"]


def build_report(sales):
    """Return one line per sale, flagging sales above the configured threshold."""
    threshold = load_threshold()
    lines = []
    for sale in sales:
        marker = "*" if sale["amount"] > threshold else " "
        lines.append(f"{marker} {sale['id']}: {sale['amount']:.2f}")
    return "\n".join(lines)
