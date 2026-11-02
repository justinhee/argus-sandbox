import os

REPORT_DIR = "/srv/reports"


def read_report(name: str) -> bytes:
    """Return the bytes of a report the user asked for by name."""
    with open(os.path.join(REPORT_DIR, name), "rb") as f:
        return f.read()
