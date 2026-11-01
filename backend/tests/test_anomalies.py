import pytest
from datetime import datetime, timedelta
from backend.app.models.entities import (
    Product, SKU, Location, InventoryBalance, Reservation,
    Allocation, Transfer, Order, OrderLine
)
from backend.app.services.anomaly_engine import AnomalyEngine
from backend.app.services.inventory_engine import InventoryEngine

def test_four_mandatory_anomalies_detected(db_session):
    now = datetime.utcnow()
    # Master data
    prod = Product(product_id="PRD-ANM", product_name="Anomaly Prod", brand="Echo", category="Hardware")
    loc_a = Location(location_id="LOC-ANM-A", location_code="LC-AA", location_name="Loc A", location_type="Warehouse", address="100 A", city="Austin", region="TX")
    loc_b = Location(location_id="LOC-ANM-B", location_code="LC-BB", location_name="Loc B", location_type="Warehouse", address="200 B", city="Dallas", region="TX")
    sku_1 = SKU(sku_id="SKU-ANM-1", product_id="PRD-ANM", sku_code="SKU-A1", variant="Red", unit_cost=10.0, selling_price=20.0)
    sku_2 = SKU(sku_id="SKU-ANM-2", product_id="PRD-ANM", sku_code="SKU-A2", variant="Blue", unit_cost=10.0, selling_price=20.0)
    sku_3 = SKU(sku_id="SKU-ANM-3", product_id="PRD-ANM", sku_code="SKU-A3", variant="Green", unit_cost=10.0, selling_price=20.0)
    sku_4 = SKU(sku_id="SKU-ANM-4", product_id="PRD-ANM", sku_code="SKU-A4", variant="Yellow", unit_cost=10.0, selling_price=20.0)
    db_session.add_all([prod, loc_a, loc_b, sku_1, sku_2, sku_3, sku_4])
    db_session.commit()

    inv = InventoryEngine(db_session)
    # Receive 100 units of SKU-1 at Loc A
    inv.record_movement(sku_id="SKU-ANM-1", destination_location_id="LOC-ANM-A", movement_type="RECEIPT", quantity=100, reference_type="PO")

    # ANOMALY 1: Balance Mismatch (force balance to 150 while movements sum is 100)
    bal_1 = db_session.query(InventoryBalance).filter_by(sku_id="SKU-ANM-1", location_id="LOC-ANM-A").first()
    bal_1.on_hand_quantity = 150
    db_session.commit()

    # ANOMALY 2: Reservation Overflow (Active reservation 500 while stock is only 50)
    inv.record_movement(sku_id="SKU-ANM-2", destination_location_id="LOC-ANM-A", movement_type="RECEIPT", quantity=50, reference_type="PO")
    order_1 = Order(order_id="ORD-01", channel="ONLINE", customer_reference="CUST-01", order_status="PENDING")
    line_1 = OrderLine(order_line_id="ORDL-01", order_id="ORD-01", sku_id="SKU-ANM-2", ordered_quantity=10, unit_price=20.0)
    db_session.add_all([order_1, line_1])
    db_session.commit()

    res = Reservation(
        reservation_id="RES-OVF-001", order_id="ORD-01", order_line_id="ORDL-01",
        sku_id="SKU-ANM-2", location_id="LOC-ANM-A", quantity=500,
        reservation_status="ACTIVE", reserved_at=now, expires_at=now + timedelta(hours=2)
    )
    db_session.add(res)
    db_session.commit()

    # ANOMALY 3: Blocked Stock Fulfillment (Allocated 20 units where all 50 units are blocked)
    inv.record_movement(sku_id="SKU-ANM-3", destination_location_id="LOC-ANM-A", movement_type="RECEIPT", quantity=50, reference_type="PO")
    bal_3 = db_session.query(InventoryBalance).filter_by(sku_id="SKU-ANM-3", location_id="LOC-ANM-A").first()
    bal_3.blocked_quantity = 50
    bal_3.available_quantity = 0

    order_2 = Order(order_id="ORD-02", channel="ONLINE", customer_reference="CUST-02", order_status="PENDING")
    line_2 = OrderLine(order_line_id="ORDL-BLK-01", order_id="ORD-02", sku_id="SKU-ANM-3", ordered_quantity=20, unit_price=20.0)
    db_session.add_all([order_2, line_2])
    db_session.commit()

    alc = Allocation(
        allocation_id="ALC-BLK-001", order_line_id="ORDL-BLK-01", sku_id="SKU-ANM-3",
        location_id="LOC-ANM-A", allocated_quantity=20, decision="ACCEPTED",
        decision_reason="TEST_ALLOCATION", allocated_at=now
    )
    db_session.add(alc)
    db_session.commit()

    # ANOMALY 4: Premature Transfer (Received without dispatch)
    trn = Transfer(
        transfer_id="TRN-PREM-001", transfer_number="TRN-NO-PREM-001",
        source_location_id="LOC-ANM-A", destination_location_id="LOC-ANM-B",
        status="COMPLETED", requested_at=now - timedelta(days=1),
        dispatched_at=None, received_at=now
    )
    db_session.add(trn)
    db_session.commit()

    # Run Detection
    anomaly_engine = AnomalyEngine(db_session)
    detected = anomaly_engine.scan_all_anomalies(persist=False)
    issue_types = {d.issue_type for d in detected}

    assert "BALANCE_MISMATCH" in issue_types
    assert "RESERVATION_OVERFLOW" in issue_types
    assert "BLOCKED_STOCK_FULFILLMENT" in issue_types
    assert "PREMATURE_TRANSFER" in issue_types
    assert len(detected) == 4
