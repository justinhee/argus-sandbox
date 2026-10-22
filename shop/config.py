"""Runtime configuration read from the environment, with typed defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = os.environ.get(name)
    if not raw:
        return list(default)
    return [part.strip() for part in raw.split(",") if part.strip()]


@dataclass(frozen=True)
class Settings:
    database_path: str = "shop.db"
    payment_gateway_url: str = "https://payments.example.com/v1"
    payment_timeout_s: int = 10
    payment_max_retries: int = 3
    token_secret: str = "change-me"
    token_ttl_s: int = 3600
    rate_limit_per_minute: int = 120
    cache_ttl_s: int = 300
    cache_max_entries: int = 1024
    smtp_host: str = "localhost"
    smtp_port: int = 25
    email_from: str = "orders@example.com"
    supported_regions: list[str] = field(default_factory=lambda: ["US-CA", "US-NY", "US-TX", "US-WA"])
    debug: bool = False


def load_settings() -> Settings:
    return Settings(
        database_path=os.environ.get("SHOP_DB_PATH", "shop.db"),
        payment_gateway_url=os.environ.get("SHOP_PAYMENT_URL", "https://payments.example.com/v1"),
        payment_timeout_s=_env_int("SHOP_PAYMENT_TIMEOUT_S", 10),
        payment_max_retries=_env_int("SHOP_PAYMENT_MAX_RETRIES", 3),
        token_secret=os.environ.get("SHOP_TOKEN_SECRET", "change-me"),
        token_ttl_s=_env_int("SHOP_TOKEN_TTL_S", 3600),
        rate_limit_per_minute=_env_int("SHOP_RATE_LIMIT_PER_MINUTE", 120),
        cache_ttl_s=_env_int("SHOP_CACHE_TTL_S", 300),
        cache_max_entries=_env_int("SHOP_CACHE_MAX_ENTRIES", 1024),
        smtp_host=os.environ.get("SHOP_SMTP_HOST", "localhost"),
        smtp_port=_env_int("SHOP_SMTP_PORT", 25),
        email_from=os.environ.get("SHOP_EMAIL_FROM", "orders@example.com"),
        supported_regions=_env_list("SHOP_REGIONS", ["US-CA", "US-NY", "US-TX", "US-WA"]),
        debug=_env_bool("SHOP_DEBUG", False),
    )
