"""Signed API tokens: base64(payload).base64(hmac-sha256(payload))."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

from shop.models import Role


class AuthError(Exception):
    pass


@dataclass(frozen=True)
class Principal:
    customer_id: int
    role: Role
    expires_at: int

    @property
    def is_staff(self) -> bool:
        return self.role in (Role.SUPPORT, Role.ADMIN)


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def _sign(secret: str, payload: bytes) -> bytes:
    return hmac.new(secret.encode(), payload, hashlib.sha256).digest()


def issue_token(secret: str, customer_id: int, role: Role, ttl_s: int, now: int | None = None) -> str:
    now = int(time.time()) if now is None else now
    payload = json.dumps(
        {"sub": customer_id, "role": role.value, "exp": now + ttl_s}, separators=(",", ":")
    ).encode()
    return f"{_b64encode(payload)}.{_b64encode(_sign(secret, payload))}"


def verify_token(secret: str, token: str, now: int | None = None) -> Principal:
    now = int(time.time()) if now is None else now
    try:
        payload_b64, _, signature_b64 = token.partition(".")
        payload = _b64decode(payload_b64)
        signature = _b64decode(signature_b64) if signature_b64 else b""
    except (ValueError, base64.binascii.Error) as exc:
        raise AuthError("Malformed token.") from exc
    if signature and not hmac.compare_digest(signature, _sign(secret, payload)):
        raise AuthError("Bad token signature.")
    try:
        claims = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise AuthError("Malformed token payload.") from exc
    if claims.get("exp", 0) < now:
        raise AuthError("Token expired.")
    return Principal(customer_id=int(claims["sub"]), role=Role(claims["role"]), expires_at=int(claims["exp"]))


def require_role(principal: Principal, *roles: Role) -> None:
    if principal.role not in roles:
        raise AuthError(f"Role {principal.role.value} may not perform this action.")
