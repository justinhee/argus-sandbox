"""Display labels for report formats offered on the downloads page."""

FORMAT_LABELS = {
    "csv": "Spreadsheet (CSV)",
    "pdf": "Printable (PDF)",
    "json": "Raw data (JSON)",
}


def label_for(fmt: str) -> str:
    return FORMAT_LABELS.get(fmt, fmt.upper())
