import os

REPORT_DIR = os.path.realpath("/srv/reports")


def read_report(name: str) -> bytes:
    """Return the bytes of a report the user asked for by name."""
    path = os.path.realpath(os.path.join(REPORT_DIR, name))
    if os.path.commonpath([path, REPORT_DIR]) != REPORT_DIR:
        raise ValueError(f"Report {name!r} is outside the report directory.")
    with open(path, "rb") as f:
        return f.read()
