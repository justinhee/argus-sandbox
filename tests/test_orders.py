from decimal import Decimal

import pytest

from shop.db import Database
from shop.inventory import Inventory
from shop.models import Customer, OrderStatus, Product
from shop.orders import InvalidTransition, OrderService


@pytest.fixture
def service(tmp_path):
    db = Database(str(tmp_path / "shop.db"))
    db.migrate()
    db.upsert_product(Product(sku="MUG", name="Mug", price=Decimal("12.00"), category="kitchen", weight_grams=400))
    db.upsert_product(Product(sku="TEE", name="T-shirt", price=Decimal("20.00"), category="apparel", weight_grams=200))
    db.add_customer(Customer(customer_id=1, email="a@example.com", name="Ada", region="US-CA"))
    inventory = Inventory()
    inventory.receive("MUG", 10)
    inventory.receive("TEE", 10)
    return OrderService(db, inventory, {"MUG": 400, "TEE": 200})


def test_place_should_price_and_reserve(service):
    order = service.create_draft(1, "US-CA", {"MUG": 2, "TEE": 1})
    placed = service.place(order.order_id, [])
    assert (placed.status, placed.tax) == (OrderStatus.PLACED, Decimal("3.19"))


def test_full_lifecycle_should_reach_delivered(service):
    order = service.create_draft(1, "US-CA", {"MUG": 1})
    service.place(order.order_id, [])
    service.mark_paid(order.order_id)
    service.ship(order.order_id)
    assert service.deliver(order.order_id).status is OrderStatus.DELIVERED


def test_draft_should_not_ship(service):
    order = service.create_draft(1, "US-CA", {"MUG": 1})
    with pytest.raises(ValueError, match="no stock reservation"):
        service.ship(order.order_id)


def test_delivered_order_should_not_cancel(service):
    order = service.create_draft(1, "US-CA", {"MUG": 1})
    service.place(order.order_id, [])
    service.mark_paid(order.order_id)
    service.ship(order.order_id)
    service.deliver(order.order_id)
    with pytest.raises(InvalidTransition):
        service.cancel(order.order_id)


def test_full_refund_quote_should_include_shipping_and_tax(service):
    order = service.create_draft(1, "US-CA", {"MUG": 1})
    placed = service.place(order.order_id, [])
    quote = service.refund_quote(order.order_id)
    assert quote.total == placed.total
