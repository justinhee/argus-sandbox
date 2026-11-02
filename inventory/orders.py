from datetime import datetime


def is_expired(expires_at: datetime) -> bool:
    """An order hold is expired once its expiry time has passed."""
    return expires_at > datetime.now()
