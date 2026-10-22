"""Background jobs: expire stale reservations, prune rate-limit buckets, flush reports."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

log = logging.getLogger(__name__)


@dataclass
class Job:
    name: str
    interval_s: float
    fn: Callable[[], object]
    next_run: float = 0.0
    runs: int = 0
    failures: int = 0


@dataclass
class Scheduler:
    tick_s: float = 1.0
    clock: Callable[[], float] = time.monotonic
    _jobs: list[Job] = field(default_factory=list)
    _stop: threading.Event = field(default_factory=threading.Event)
    _thread: threading.Thread | None = None

    def every(self, interval_s: float, name: str, fn: Callable[[], object]) -> Job:
        if interval_s <= 0:
            raise ValueError("interval_s must be positive.")
        job = Job(name=name, interval_s=interval_s, fn=fn, next_run=self.clock())
        self._jobs.append(job)
        return job

    def run_pending(self) -> int:
        now = self.clock()
        ran = 0
        for job in self._jobs:
            if job.next_run <= now:
                job.fn()
                job.runs += 1
                job.next_run = now + job.interval_s
                ran += 1
        return ran

    def _loop(self) -> None:
        while not self._stop.is_set():
            self.run_pending()
            self._stop.wait(self.tick_s)

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="shop-scheduler", daemon=True)
        self._thread.start()

    def stop(self, timeout_s: float = 5.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout_s)
            self._thread = None
