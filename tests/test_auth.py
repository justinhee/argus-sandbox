import pytest

from shop.auth import AuthError, issue_token, require_role, verify_token
from shop.models import Role

SECRET = "test-secret"


def test_verify_token_should_round_trip_claims():
    token = issue_token(SECRET, 42, Role.CUSTOMER, ttl_s=60, now=1000)
    principal = verify_token(SECRET, token, now=1010)
    assert (principal.customer_id, principal.role) == (42, Role.CUSTOMER)


def test_verify_token_should_reject_wrong_secret():
    token = issue_token(SECRET, 42, Role.CUSTOMER, ttl_s=60, now=1000)
    with pytest.raises(AuthError, match="signature"):
        verify_token("other", token, now=1010)


def test_verify_token_should_reject_expired_token():
    token = issue_token(SECRET, 42, Role.CUSTOMER, ttl_s=60, now=1000)
    with pytest.raises(AuthError, match="expired"):
        verify_token(SECRET, token, now=2000)


def test_require_role_should_reject_customer_for_admin_action():
    principal = verify_token(SECRET, issue_token(SECRET, 1, Role.CUSTOMER, 60, now=0), now=1)
    with pytest.raises(AuthError, match="may not"):
        require_role(principal, Role.ADMIN)
