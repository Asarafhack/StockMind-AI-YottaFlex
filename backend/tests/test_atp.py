import pytest
from datetime import datetime, timedelta
from backend.app.models.entities import (
    Product, SKU, Location, InventoryBalance, InventoryMovement,
    Reservation, ReplenishmentRule, Transfer, TransferLine, Order, OrderLine
)
from backend.app.services.atp_engine import ATPEngine
from backend.app.services.inventory_engine import InventoryEngine

def test_atp_standard_formula(db_session):
    now = datetime.utcnow()
    # 1. Setup Master Data
    prod = Product(product_id="PRD-001", product_name="Test Prod", brand="Apex", category="Electronics")
    loc = Location(location_id="LOC-001", location_code="LC-01", location_name="Main DC", location_type="Distribution Center", address="100 Way", city="New York", region="NY")
    sku = SKU(sku_id="SKU-001", product_id="PRD-001", sku_code="SKU-TEST-001", variant="Standard", unit_cost=50.0, selling_price=100.0)
    db_session.add_all([prod, loc, sku])
    db_session.commit()

    # 2. Record Inbound Movement (100 units)
    inv_engine = InventoryEngine(db_session)
    inv_engine.record_movement(
        sku_id="SKU-001",
        destination_location_id="LOC-001",
        movement_type="RECEIPT",
        quantity=100,
        reference_type="PO",
        reference_id="PO-001"
    )

    # 3. Block 15 units
    bal = db_session.query(InventoryBalance).filter_by(sku_id="SKU-001", location_id="LOC-001").first()
    bal.blocked_quantity = 15
    db_session.commit()

    # 4. Create Active Reservation of 20 units
    order = Product.__table__.metadata.tables["orders"]
    order_obj = Order(order_id="ORD-001", channel="ONLINE", customer_reference="CUST-001", order_status="PENDING")
    line_obj = OrderLine(order_line_id="ORDL-001", order_id="ORD-001", sku_id="SKU-001", ordered_quantity=20, unit_price=100.0)
    db_session.add_all([order_obj, line_obj])
    db_session.commit()

    res = Reservation(
        reservation_id="RES-001",
        order_id="ORD-001",
        order_line_id="ORDL-001",
        sku_id="SKU-001",
        location_id="LOC-001",
        quantity=20,
        reservation_status="ACTIVE",
        reserved_at=now,
        expires_at=now + timedelta(hours=2)
    )
    db_session.add(res)
    db_session.commit()

    # 5. Calculate ATP: OH (100) - R (20) - B (15) + Inbound (0) = 65
    atp_engine = ATPEngine(db_session)
    atp = atp_engine.calculate_atp("SKU-001", "LOC-001")

    assert atp.on_hand_stock == 100
    assert atp.reserved_stock == 20
    assert atp.blocked_stock == 15
    assert atp.eligible_inbound == 0
    assert atp.final_atp == 65

def test_atp_with_eligible_inbound_transfer(db_session):
    now = datetime.utcnow()
    prod = Product(product_id="PRD-002", product_name="Test Prod 2", brand="Apex", category="Electronics")
    loc_src = Location(location_id="LOC-SRC", location_code="LC-SRC", location_name="Source DC", location_type="Warehouse", address="100 Way", city="Chicago", region="IL")
    loc_dest = Location(location_id="LOC-DEST", location_code="LC-DST", location_name="Dest DC", location_type="Fulfillment Center", address="200 Way", city="Dallas", region="TX")
    sku = SKU(sku_id="SKU-002", product_id="PRD-002", sku_code="SKU-TEST-002", variant="Standard", unit_cost=30.0, selling_price=70.0)
    
    # Replenishment rule allowing confirmed in-transit
    rule = ReplenishmentRule(
        rule_id="RPL-001", sku_id="SKU-002", location_id="LOC-DEST",
        minimum_stock=10, maximum_stock=200, reorder_point=30, safety_stock=10,
        lead_time_days=3, reorder_quantity=50, inbound_eligibility_policy="ALLOW_CONFIRMED_IN_TRANSIT"
    )
    db_session.add_all([prod, loc_src, loc_dest, sku, rule])
    db_session.commit()

    # Dest has 50 on-hand
    inv_engine = InventoryEngine(db_session)
    inv_engine.record_movement(sku_id="SKU-002", destination_location_id="LOC-DEST", movement_type="RECEIPT", quantity=50, reference_type="PO")

    # Inbound transfer of 30 units in transit with tracking
    trn = Transfer(
        transfer_id="TRN-001", transfer_number="TRN-NO-001",
        source_location_id="LOC-SRC", destination_location_id="LOC-DEST",
        status="IN_TRANSIT", requested_at=now, dispatched_at=now, tracking_reference="TRK-FEDEX-123"
    )
    db_session.add(trn)
    db_session.flush()

    trn_line = TransferLine(
        transfer_line_id="TRNL-001", transfer_id="TRN-001", sku_id="SKU-002",
        requested_quantity=30, dispatched_quantity=30, received_quantity=0
    )
    db_session.add(trn_line)
    db_session.commit()

    atp_engine = ATPEngine(db_session)
    atp = atp_engine.calculate_atp("SKU-002", "LOC-DEST")

    # ATP = OH (50) - R (0) - B (0) + Inbound (30) = 80
    assert atp.on_hand_stock == 50
    assert atp.eligible_inbound == 30
    assert atp.final_atp == 80

def test_atp_policy_strict_on_hand_only(db_session):
    now = datetime.utcnow()
    prod = Product(product_id="PRD-003", product_name="Test Prod 3", brand="Apex", category="Electronics")
    loc_src = Location(location_id="LOC-SRC-2", location_code="LC-S2", location_name="Source 2", location_type="Warehouse", address="100 Way", city="Chicago", region="IL")
    loc_dest = Location(location_id="LOC-DEST-2", location_code="LC-D2", location_name="Dest 2", location_type="Fulfillment Center", address="200 Way", city="Dallas", region="TX")
    sku = SKU(sku_id="SKU-003", product_id="PRD-003", sku_code="SKU-TEST-003", variant="Standard", unit_cost=30.0, selling_price=70.0)
    
    # Replenishment rule STRICT_ON_HAND_ONLY
    rule = ReplenishmentRule(
        rule_id="RPL-002", sku_id="SKU-003", location_id="LOC-DEST-2",
        minimum_stock=10, maximum_stock=200, reorder_point=30, safety_stock=10,
        lead_time_days=3, reorder_quantity=50, inbound_eligibility_policy="STRICT_ON_HAND_ONLY"
    )
    db_session.add_all([prod, loc_src, loc_dest, sku, rule])
    db_session.commit()

    inv_engine = InventoryEngine(db_session)
    inv_engine.record_movement(sku_id="SKU-003", destination_location_id="LOC-DEST-2", movement_type="RECEIPT", quantity=40, reference_type="PO")

    # Inbound transfer of 50 units in transit with tracking
    trn = Transfer(
        transfer_id="TRN-002", transfer_number="TRN-NO-002",
        source_location_id="LOC-SRC-2", destination_location_id="LOC-DEST-2",
        status="IN_TRANSIT", requested_at=now, dispatched_at=now, tracking_reference="TRK-UPS-999"
    )
    db_session.add(trn)
    db_session.flush()

    trn_line = TransferLine(
        transfer_line_id="TRNL-002", transfer_id="TRN-002", sku_id="SKU-003",
        requested_quantity=50, dispatched_quantity=50, received_quantity=0
    )
    db_session.add(trn_line)
    db_session.commit()

    atp_engine = ATPEngine(db_session)
    atp = atp_engine.calculate_atp("SKU-003", "LOC-DEST-2")

    # Inbound transfer must be IGNORED under STRICT_ON_HAND_ONLY
    assert atp.on_hand_stock == 40
    assert atp.eligible_inbound == 0
    assert atp.final_atp == 40

def test_atp_zero_clamping_boundary(db_session):
    now = datetime.utcnow()
    prod = Product(product_id="PRD-004", product_name="Test Prod 4", brand="Apex", category="Electronics")
    loc = Location(location_id="LOC-004", location_code="LC-04", location_name="DC 4", location_type="Warehouse", address="100 Way", city="Atlanta", region="GA")
    sku = SKU(sku_id="SKU-004", product_id="PRD-004", sku_code="SKU-TEST-004", variant="Standard", unit_cost=10.0, selling_price=20.0)
    db_session.add_all([prod, loc, sku])
    db_session.commit()

    inv_engine = InventoryEngine(db_session)
    inv_engine.record_movement(sku_id="SKU-004", destination_location_id="LOC-004", movement_type="RECEIPT", quantity=20, reference_type="PO")

    # Block 30 units (more than on-hand)
    bal = db_session.query(InventoryBalance).filter_by(sku_id="SKU-004", location_id="LOC-004").first()
    bal.blocked_quantity = 30
    db_session.commit()

    atp_engine = ATPEngine(db_session)
    atp = atp_engine.calculate_atp("SKU-004", "LOC-004")

    # ATP must clamp to 0, never negative
    assert atp.on_hand_stock == 20
    assert atp.blocked_stock == 30
    assert atp.final_atp == 0
    assert atp.reservable_stock == 0

def test_atp_excludes_expired_reservations(db_session):
    now = datetime.utcnow()
    prod = Product(product_id="PRD-005", product_name="Test Prod 5", brand="Apex", category="Electronics")
    loc = Location(location_id="LOC-005", location_code="LC-05", location_name="DC 5", location_type="Warehouse", address="100 Way", city="Seattle", region="WA")
    sku = SKU(sku_id="SKU-005", product_id="PRD-005", sku_code="SKU-TEST-005", variant="Standard", unit_cost=10.0, selling_price=20.0)
    db_session.add_all([prod, loc, sku])
    db_session.commit()

    inv_engine = InventoryEngine(db_session)
    inv_engine.record_movement(sku_id="SKU-005", destination_location_id="LOC-005", movement_type="RECEIPT", quantity=50, reference_type="PO")

    order = Order(order_id="ORD-EXP-01", channel="ONLINE", customer_reference="CUST-EXP", order_status="PENDING")
    line = OrderLine(order_line_id="ORDL-EXP-01", order_id="ORD-EXP-01", sku_id="SKU-005", ordered_quantity=15, unit_price=20.0)
    db_session.add_all([order, line])
    db_session.commit()

    # Expired reservation (expires_at is 1 hour ago)
    res = Reservation(
        reservation_id="RES-EXP-01", order_id="ORD-EXP-01", order_line_id="ORDL-EXP-01",
        sku_id="SKU-005", location_id="LOC-005", quantity=15,
        reservation_status="ACTIVE", reserved_at=now - timedelta(hours=2),
        expires_at=now - timedelta(hours=1)
    )
    db_session.add(res)
    db_session.commit()

    atp_engine = ATPEngine(db_session)
    atp = atp_engine.calculate_atp("SKU-005", "LOC-005")

    # Expired reservation must not reduce ATP
    assert atp.reserved_stock == 0
    assert atp.final_atp == 50
