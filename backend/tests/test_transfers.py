import pytest
from backend.app.models.entities import Product, SKU, Location, InventoryBalance, Transfer
from backend.app.services.transfer_engine import TransferEngine
from backend.app.services.inventory_engine import InventoryEngine

def test_transfer_lifecycle_and_zero_double_counting(db_session):
    prod = Product(product_id="PRD-TRN", product_name="Trn Prod", brand="Terra", category="Tools")
    loc_a = Location(location_id="LOC-WH-A", location_code="LC-WHA", location_name="Warehouse A", location_type="Warehouse", address="100 West", city="Phoenix", region="AZ")
    loc_b = Location(location_id="LOC-WH-B", location_code="LC-WHB", location_name="Warehouse B", location_type="Warehouse", address="200 East", city="Denver", region="CO")
    sku = SKU(sku_id="SKU-TRN-01", product_id="PRD-TRN", sku_code="SKU-TRN-01", variant="Heavy", unit_cost=40.0, selling_price=90.0)
    db_session.add_all([prod, loc_a, loc_b, sku])
    db_session.commit()

    inv = InventoryEngine(db_session)
    # Location A receives 100 units; Location B has 0
    inv.record_movement(sku_id="SKU-TRN-01", destination_location_id="LOC-WH-A", movement_type="RECEIPT", quantity=100, reference_type="PO")

    bal_a = db_session.query(InventoryBalance).filter_by(sku_id="SKU-TRN-01", location_id="LOC-WH-A").first()
    bal_b = inv._get_or_create_balance("SKU-TRN-01", "LOC-WH-B")
    db_session.commit()

    assert bal_a.on_hand_quantity == 100
    assert bal_b.on_hand_quantity == 0

    # 1. Create Transfer of 30 units
    trn_engine = TransferEngine(db_session)
    trn = trn_engine.create_transfer(
        source_location_id="LOC-WH-A",
        destination_location_id="LOC-WH-B",
        lines=[{"sku_id": "SKU-TRN-01", "requested_quantity": 30}],
        carrier="Internal Fleet"
    )
    assert trn.status == "CREATED"

    # 2. Dispatch Transfer
    dispatch_res = trn_engine.dispatch_transfer(trn.transfer_id, tracking_reference="FLEET-777")
    assert dispatch_res["success"] is True

    db_session.refresh(bal_a)
    db_session.refresh(bal_b)

    # In-transit assertion:
    # A has 70 on-hand (deducted 30)
    # B has 0 on-hand and 30 in-transit!
    # Total on-hand across enterprise is exactly 70. Never 100 simultaneously available!
    assert bal_a.on_hand_quantity == 70
    assert bal_b.on_hand_quantity == 0
    assert bal_b.in_transit_quantity == 30

    # 3. Receive Transfer at Location B
    rec_res = trn_engine.receive_transfer(trn.transfer_id)
    assert rec_res["success"] is True

    db_session.refresh(bal_a)
    db_session.refresh(bal_b)

    # Completed state:
    # A has 70, B has 30, B in-transit is 0
    # Total on-hand is 100
    assert bal_a.on_hand_quantity == 70
    assert bal_b.on_hand_quantity == 30
    assert bal_b.in_transit_quantity == 0
    assert trn.status == "COMPLETED"
