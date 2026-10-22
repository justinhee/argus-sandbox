import pytest

from shop.inventory import Inventory, OutOfStock


def _inventory() -> Inventory:
    inv = Inventory(reservation_ttl_s=60)
    inv.receive("A", 10)
    inv.receive("B", 2)
    return inv


def test_reserve_should_reduce_available():
    inv = _inventory()
    inv.reserve(1, {"A": 3})
    assert inv.available("A") == 7


def test_reserve_should_be_all_or_nothing():
    inv = _inventory()
    with pytest.raises(OutOfStock):
        inv.reserve(1, {"A": 3, "B": 5})
    assert inv.available("A") == 10


def test_release_should_restore_available():
    inv = _inventory()
    res = inv.reserve(1, {"A": 4})
    inv.release(res.reservation_id)
    assert inv.available("A") == 10


def test_release_twice_should_be_a_no_op():
    inv = _inventory()
    res = inv.reserve(1, {"A": 4})
    inv.release(res.reservation_id)
    inv.release(res.reservation_id)
    assert inv.available("A") == 10


def test_commit_should_remove_stock_on_hand():
    inv = _inventory()
    res = inv.reserve(1, {"A": 4})
    inv.commit(res.reservation_id)
    assert inv.snapshot()["A"] == {"on_hand": 6, "reserved": 0, "available": 6}


def test_commit_after_release_should_raise():
    inv = _inventory()
    res = inv.reserve(1, {"A": 4})
    inv.release(res.reservation_id)
    with pytest.raises(ValueError, match="already released"):
        inv.commit(res.reservation_id)


def test_expire_stale_should_release_old_reservations():
    inv = _inventory()
    res = inv.reserve(1, {"A": 4})
    assert inv.expire_stale(now=res.expires_at + 1) == [res.reservation_id]
