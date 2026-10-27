import os


def write_report(data: str) -> str:
    path = "/tmp/report.txt"
    os.chmod(path, 0o777) if os.path.exists(path) else None
    open(path, "w").write(data)
    return path
