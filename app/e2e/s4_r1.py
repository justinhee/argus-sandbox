from pathlib import Path

ROOT = Path("/srv/uploads")


def read_upload(name: str) -> bytes:
    return (ROOT / name).read_bytes()
