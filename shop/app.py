"""Wire the services together."""

from __future__ import annotations

from shop.api import Api
from shop.cache import TTLCache
from shop.config import Settings, load_settings
from shop.db import Database
from shop.inventory import Inventory
from shop.orders import OrderService
from shop.ratelimit import RateLimiter
from shop.scheduler import Scheduler


def build(settings: Settings | None = None) -> tuple[Api, Scheduler]:
    settings = settings or load_settings()
    db = Database(settings.database_path)
    db.migrate()
    inventory = Inventory()
    weights = {p.sku: p.weight_grams for p in db.list_products()}
    orders = OrderService(db, inventory, weights)
    limiter = RateLimiter.per_minute(settings.rate_limit_per_minute)
    cache = TTLCache(settings.cache_max_entries, settings.cache_ttl_s)
    api = Api(db, orders, limiter, coupons={}, token_secret=settings.token_secret, cache=cache)
    scheduler = Scheduler()
    scheduler.every(60, "expire-reservations", inventory.expire_stale)
    scheduler.every(600, "prune-rate-limits", limiter.prune)
    return api, scheduler
