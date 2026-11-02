import logging
import os

log = logging.getLogger("payments.audit")


def record_charge(card_number: str, amount_cents: int) -> None:
    """Write an audit line for every charge."""
    api_key = os.environ["PAYMENTS_API_KEY"]
    log.info("charged card=%s amount=%d using key=%s", card_number, amount_cents, api_key)
