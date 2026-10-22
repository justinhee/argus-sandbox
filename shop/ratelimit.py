"""Per-client token bucket rate limiter."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class _Bucket:
    tokens: float
    updated_at: float


@dataclass
class RateLimiter:
    capacity: int
    refill_per_second: float
    clock: callable = time.monotonic
    _buckets: dict[str, _Bucket] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    @classmethod
    def per_minute(cls, limit: int) -> "RateLimiter":
        return cls(capacity=limit, refill_per_second=limit / 60)

    def allow(self, client_id: str, cost: float = 1.0) -> bool:
        now = self.clock()
        with self._lock:
            bucket = self._buckets.get(client_id)
            if bucket is None:
                bucket = _Bucket(tokens=float(self.capacity), updated_at=now)
                self._buckets[client_id] = bucket
            elapsed = now - bucket.updated_at
            bucket.tokens = min(self.capacity, bucket.tokens + elapsed * self.refill_per_second)
            bucket.updated_at = now
            if bucket.tokens >= cost:
                bucket.tokens -= cost
                return True
            return False

    def retry_after(self, client_id: str, cost: float = 1.0) -> float:
        with self._lock:
            bucket = self._buckets.get(client_id)
            if bucket is None or bucket.tokens >= cost:
                return 0.0
            return (cost - bucket.tokens) / self.refill_per_second

    def prune(self, idle_s: float = 3600.0) -> int:
        now = self.clock()
        with self._lock:
            stale = [cid for cid, b in self._buckets.items() if now - b.updated_at > idle_s]
            for cid in stale:
                del self._buckets[cid]
            return len(stale)
