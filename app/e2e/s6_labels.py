STATUS_LABELS = {"open": "Open", "closed": "Closed"}


def status_label(code: str) -> str:
    return STATUS_LABELS.get(code, code)
