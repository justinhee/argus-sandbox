"""Unit labels shown next to stock counts."""

UNIT_LABELS = {"ea": "each", "bx": "box", "pk": "pack"}


def unit_label(code: str) -> str:
    return UNIT_LABELS.get(code, code)
