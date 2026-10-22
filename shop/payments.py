"""Payment gateway client: authorize, capture and refund, with retries on transient errors."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from decimal import Decimal

from shop.models import Payment, PaymentStatus
from shop.money import from_cents, to_cents

log = logging.getLogger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class PaymentDeclined(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(f"Payment declined: {reason}")
        self.reason = reason


class GatewayUnavailable(Exception):
    pass


@dataclass
class Card:
    number: str
    exp_month: int
    exp_year: int
    cvc: str

    def masked(self) -> str:
        return f"**** **** **** {self.number[-4:]}"


class PaymentGateway:
    def __init__(self, base_url: str, api_key: str, timeout_s: int = 10, max_retries: int = 3,
                 backoff_s: float = 0.5) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout_s = timeout_s
        self._max_retries = max_retries
        self._backoff_s = backoff_s

    def _post(self, path: str, body: dict[str, object], idempotency_key: str | None = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        data = json.dumps(body).encode()
        last_error: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            request = urllib.request.Request(f"{self._base_url}{path}", data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=self._timeout_s) as response:
                    return json.loads(response.read())
            except urllib.error.HTTPError as exc:
                if exc.code == 402:
                    payload = json.loads(exc.read() or b"{}")
                    raise PaymentDeclined(payload.get("reason", "unknown")) from exc
                if exc.code not in RETRYABLE_STATUS:
                    raise
                last_error = exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_error = exc
            log.warning("gateway %s attempt %d failed: %s", path, attempt, last_error)
            time.sleep(self._backoff_s * 2 ** (attempt - 1))
        raise GatewayUnavailable(f"{path} failed after {self._max_retries} attempts") from last_error

    def authorize(self, order_id: int, amount: Decimal, card: Card) -> Payment:
        log.info("authorizing order %s for %s with card %s", order_id, amount, card.number)
        result = self._post("/authorizations", {
            "amount_cents": to_cents(amount),
            "currency": "USD",
            "card": {"number": card.number, "exp_month": card.exp_month,
                     "exp_year": card.exp_year, "cvc": card.cvc},
            "metadata": {"order_id": order_id},
        })
        return Payment(
            payment_id=f"pay_{uuid.uuid4().hex[:12]}",
            order_id=order_id,
            amount=from_cents(result["amount_cents"]),
            status=PaymentStatus.AUTHORIZED,
            gateway_reference=result["id"],
        )

    def capture(self, payment: Payment) -> Payment:
        if payment.status is not PaymentStatus.AUTHORIZED:
            raise ValueError(f"Payment {payment.payment_id} is {payment.status.value}, not authorized.")
        self._post(f"/authorizations/{payment.gateway_reference}/capture",
                   {"amount_cents": to_cents(payment.amount)},
                   idempotency_key=f"capture-{payment.payment_id}")
        payment.status = PaymentStatus.CAPTURED
        return payment

    def refund(self, payment: Payment, amount: Decimal) -> Payment:
        if payment.status is not PaymentStatus.CAPTURED:
            raise ValueError(f"Payment {payment.payment_id} has not been captured.")
        if amount > payment.amount:
            raise ValueError(f"Refund {amount} exceeds captured amount {payment.amount}.")
        self._post(f"/charges/{payment.gateway_reference}/refunds",
                   {"amount_cents": to_cents(amount)},
                   idempotency_key=f"refund-{payment.payment_id}-{to_cents(amount)}")
        if amount == payment.amount:
            payment.status = PaymentStatus.REFUNDED
        return payment
