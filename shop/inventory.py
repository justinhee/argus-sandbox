"""Stock levels and reservations. Reservations hold stock while an order is unpaid."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


class OutOfStock(Exception):
    def __init__(self, sku: str, requested: int, available: int) -> None:
        super().__init__(f"{sku}: requested {requested}, only {available} available.")
        self.sku = sku
        self.requested = requested
        self.available = available


@dataclass
class Reservation:
    reservation_id: str
    order_id: int
    items: dict[str, int]
    expires_at: float
    released: bool = False


@dataclass
class StockLevel:
    on_hand: int = 0
    reserved: int = 0

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved


@dataclass
class Inventory:
    reservation_ttl_s: float = 900.0
    _stock: dict[str, StockLevel] = field(default_factory=dict)
    _reservations: dict[str, Reservation] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _counter: int = 0

    def receive(self, sku: str, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Received quantity must be positive.")
        with self._lock:
            self._stock.setdefault(sku, StockLevel()).on_hand += quantity

    def available(self, sku: str) -> int:
        with self._lock:
            level = self._stock.get(sku)
            return level.available if level else 0

    def reserve(self, order_id: int, items: dict[str, int]) -> Reservation:
        """Reserve every item or none of them."""
        for sku, qty in items.items():
            available = self.available(sku)
            if qty > available:
                raise OutOfStock(sku, qty, available)
        with self._lock:
            for sku, qty in items.items():
                self._stock.setdefault(sku, StockLevel()).reserved += qty
            self._counter += 1
            reservation = Reservation(
                reservation_id=f"res-{self._counter}",
                order_id=order_id,
                items=dict(items),
                expires_at=time.monotonic() + self.reservation_ttl_s,
            )
            self._reservations[reservation.reservation_id] = reservation
            return reservation

    def release(self, reservation_id: str) -> None:
        with self._lock:
            reservation = self._reservations.get(reservation_id)
            if reservation is None or reservation.released:
                return
            for sku, qty in reservation.items.items():
                self._stock[sku].reserved -= qty
            reservation.released = True

    def commit(self, reservation_id: str) -> None:
        """Turn a reservation into a shipment: stock leaves the building."""
        with self._lock:
            reservation = self._reservations.get(reservation_id)
            if reservation is None:
                raise KeyError(f"Unknown reservation {reservation_id}.")
            if reservation.released:
                raise ValueError(f"Reservation {reservation_id} was already released.")
            for sku, qty in reservation.items.items():
                level = self._stock[sku]
                level.reserved -= qty
                level.on_hand -= qty
            reservation.released = True

    def expire_stale(self, now: float | None = None) -> list[str]:
        now = time.monotonic() if now is None else now
        expired: list[str] = []
        with self._lock:
            for rid, reservation in self._reservations.items():
                if not reservation.released and reservation.expires_at <= now:
                    for sku, qty in reservation.items.items():
                        self._stock[sku].reserved -= qty
                    reservation.released = True
                    expired.append(rid)
        return expired

    def snapshot(self) -> dict[str, dict[str, int]]:
        with self._lock:
            return {
                sku: {"on_hand": lvl.on_hand, "reserved": lvl.reserved, "available": lvl.available}
                for sku, lvl in self._stock.items()
            }
