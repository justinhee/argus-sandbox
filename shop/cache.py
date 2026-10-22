"""Small in-process LRU cache with per-entry TTL, used for catalog reads."""

from __future__ import annotations

import functools
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class TTLCache:
    def __init__(self, max_entries: int = 1024, ttl_s: float = 300.0,
                 clock: Callable[[], float] = time.monotonic) -> None:
        if max_entries <= 0:
            raise ValueError("max_entries must be positive.")
        self._max = max_entries
        self._ttl = ttl_s
        self._clock = clock
        self._data: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                self.misses += 1
                return None
            expires_at, value = entry
            if expires_at < self._clock():
                del self._data[key]
                self.misses += 1
                return None
            self._data.move_to_end(key)
            self.hits += 1
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = (self._clock() + self._ttl, value)
            self._data.move_to_end(key)
            while len(self._data) > self._max:
                self._data.popitem(last=False)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


def cached(cache: TTLCache) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Memoize a function's result in the given cache."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            key = f"{fn.__module__}.{fn.__qualname__}:{args!r}"
            hit = cache.get(key)
            if hit is not None:
                return hit
            value = fn(*args, **kwargs)
            cache.set(key, value)
            return value

        return wrapper

    return decorator
