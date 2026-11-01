import pytest
from datetime import datetime, timedelta
from backend.app.models.entities import (
    Product, SKU, Location, InventoryBalance, Order, OrderLine, Reservation
)
from backend.app.services.reservation_engine import ReservationEngine
from backend.app.services.inventory_engine import InventoryEngine

def test_reservation_lifecycle_and_expiry(db_session):
    now = datetime.utcnow()
    # 1. Setup master data
    prod = Product(product_id="PRD-RES-01", product_name="Res Prod", brand="Nordic", category="Apparel")
    loc = Location(location_id="LOC-RES-01", location_code="LC-R1", location_name="Store 1", location_type="Retail Store", address="1 Main St", city="Boston", region="MA")
    sku = SKU(sku_id="SKU-RES-01", product_id="PRD-RES-01", sku_code="SKU-R1", variant="Blue", unit_cost=20.0, selling_price=50.0)
    db_session.add_all([prod, loc, sku])
    db_session.commit()

    # Receive 100 units
    inv = InventoryEngine(db_session)
    inv.record_movement(sku_id="SKU-RES-01", destination_location_id="LOC-RES-01", movement_type="RECEIPT", quantity=100, reference_type="PO")

    # Order
    order = Order(order_id="ORD-TEST-001", channel="ONLINE", customer_reference="CUST-001", order_status="PENDING", total_amount=100.0)
    line = OrderLine(order_line_id="ORDL-TEST-001-01", order_id="ORD-TEST-001", sku_id="SKU-RES-01", ordered_quantity=15, unit_price=50.0)
    db_session.add_all([order, line])
    db_session.commit()

    # Create Reservation of 15 units
    res_engine = ReservationEngine(db_session)
    res_result = res_engine.create_reservation(
        order_id="ORD-TEST-001",
        order_line_id="ORDL-TEST-001-01",
        sku_id="SKU-RES-01",
        location_id="LOC-RES-01",
        quantity=15,
        duration_minutes=60
    )
    assert res_result["success"] is True
    res_obj = res_result["reservation"]

    # Balance check: reserved_quantity should be 15, available should be 85
    bal = db_session.query(InventoryBalance).filter_by(sku_id="SKU-RES-01", location_id="LOC-RES-01").first()
    assert bal.reserved_quantity == 15
    assert bal.available_quantity == 85

    # Simulate expiration by moving expires_at to the past
    res_obj.expires_at = now - timedelta(minutes=5)
    db_session.commit()

    # Run sweep
    expired_count = res_engine.expire_stale_reservations()
    assert expired_count == 1

    # Verify status changed and reserved quantity was restored
    db_session.refresh(res_obj)
    db_session.refresh(bal)
    assert res_obj.reservation_status == "EXPIRED"
    assert bal.reserved_quantity == 0
    assert bal.available_quantity == 100

def test_negative_oversell_rejection(db_session):
    prod = Product(product_id="PRD-NEG", product_name="Neg Prod", brand="Nordic", category="Apparel")
    loc = Location(location_id="LOC-NEG", location_code="LC-NEG", location_name="Store Neg", location_type="Retail Store", address="1 Main St", city="Boston", region="MA")
    sku = SKU(sku_id="SKU-NEG", product_id="PRD-NEG", sku_code="SKU-NEG", variant="Blue", unit_cost=20.0, selling_price=50.0)
    db_session.add_all([prod, loc, sku])
    db_session.commit()

    # Stock is only 10 units
    inv = InventoryEngine(db_session)
    inv.record_movement(sku_id="SKU-NEG", destination_location_id="LOC-NEG", movement_type="RECEIPT", quantity=10, reference_type="PO")

    res_engine = ReservationEngine(db_session)
    result = res_engine.create_reservation(
        order_id="ORD-NEG-001",
        order_line_id="ORDL-NEG-01",
        sku_id="SKU-NEG",
        location_id="LOC-NEG",
        quantity=50  # Requesting 50 when only 10 available
    )
    assert result["success"] is False
    assert "Insufficient reservable stock" in result["error"]
