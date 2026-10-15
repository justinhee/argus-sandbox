import base64
import pickle
from pathlib import Path

EXPORT_ROOT = Path("/srv/exports")


def load_export_session(cookie: str):
    return pickle.loads(base64.b64decode(cookie))


def read_export(name: str) -> bytes:
    return (EXPORT_ROOT / name).read_bytes()
