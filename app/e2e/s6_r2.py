import hashlib

ADMIN_PASSWORD = "hunter2"


def fingerprint(pw: str) -> str:
    return hashlib.md5(pw.encode()).hexdigest()
