import pytest
from backend.app.models.entities import Product, SKU, Location, InventoryBalance, Order, OrderLine, Shipment
from backend.app.services.order_engine import OrderEngine
from backend.app.services.inventory_engine import InventoryEngine

def test_order_allocation_and_fulfillment(db_session):
    prod = Product(product_id="PRD-ORD", product_name="Order Prod", brand="Lumina", category="Decor")
    loc1 = Location(location_id="LOC-FC-1", location_code="LC-FC1", location_name="FC East", location_type="Fulfillment Center", address="100 East", city="Miami", region="FL")
    sku = SKU(sku_id="SKU-ORD-01", product_id="PRD-ORD", sku_code="SKU-ORD-01", variant="Gold", unit_cost=15.0, selling_price=35.0)
    db_session.add_all([prod, loc1, sku])
    db_session.commit()

    inv = InventoryEngine(db_session)
    inv.record_movement(sku_id="SKU-ORD-01", destination_location_id="LOC-FC-1", movement_type="RECEIPT", quantity=80, reference_type="PO")

    order_engine = OrderEngine(db_session)
    # 1. Create order for 10 units
    order_res = order_engine.create_order(
        customer_reference="CUST-VIP-001",
        lines=[{"sku_id": "SKU-ORD-01", "ordered_quantity": 10, "unit_price": 35.0}],
        auto_allocate=True
    )
    order = order_res["order"]
    assert order.order_status == "ALLOCATED"
    assert len(order_res["allocations"]) == 1
    assert order_res["allocations"][0]["decision"] == "ACCEPTED"
    assert order_res["allocations"][0]["allocated_quantity"] == 10

    # 2. Fulfill order
    fulfill_res = order_engine.fulfill_order(order.order_id, carrier="FedEx Ground")
    assert fulfill_res["success"] is True
    assert fulfill_res["fulfilled_lines"] == 1

    db_session.refresh(order)
    assert order.order_status == "SHIPPED"

    # Verify inventory was decremented via SALE movement
    bal = db_session.query(InventoryBalance).filter_by(sku_id="SKU-ORD-01", location_id="LOC-FC-1").first()
    assert bal.on_hand_quantity == 70
    assert bal.reserved_quantity == 0
    assert bal.available_quantity == 70

    # Verify shipment created
    shp = db_session.query(Shipment).filter_by(order_id=order.order_id).first()
    assert shp is not None
    assert shp.shipment_status == "SHIPPED"

def test_order_backorder_when_insufficient_stock(db_session):
    prod = Product(product_id="PRD-BKORD", product_name="Backorder Prod", brand="Apex", category="Electronics")
    loc = Location(location_id="LOC-FC-2", location_code="LC-FC2", location_name="FC West", location_type="Fulfillment Center", address="200 West", city="Denver", region="CO")
    sku = SKU(sku_id="SKU-BKORD-01", product_id="PRD-BKORD", sku_code="SKU-BK-01", variant="Silver", unit_cost=25.0, selling_price=60.0)
    sku_zero = SKU(sku_id="SKU-BKORD-02", product_id="PRD-BKORD", sku_code="SKU-BK-02", variant="Gold", unit_cost=25.0, selling_price=60.0)
    db_session.add_all([prod, loc, sku, sku_zero])
    db_session.commit()

    # Location only has 5 units for SKU-BKORD-01, and 0 for SKU-BKORD-02
    inv = InventoryEngine(db_session)
    inv.record_movement(sku_id="SKU-BKORD-01", destination_location_id="LOC-FC-2", movement_type="RECEIPT", quantity=5, reference_type="PO")

    order_engine = OrderEngine(db_session)
    # Order 1: Partial allocation (5 available out of 100) -> PARTIALLY_ALLOCATED
    order_res1 = order_engine.create_order(
        customer_reference="CUST-PARTIAL",
        lines=[{"sku_id": "SKU-BKORD-01", "ordered_quantity": 100, "unit_price": 60.0}],
        auto_allocate=True
    )
    assert order_res1["order"].order_status == "PARTIALLY_ALLOCATED"
    assert order_res1["allocations"][0]["allocated_quantity"] == 5

    # Order 2: Zero stock available (0 available out of 50) -> BACKORDERED
    order_res2 = order_engine.create_order(
        customer_reference="CUST-FULL-BACKORDER",
        lines=[{"sku_id": "SKU-BKORD-02", "ordered_quantity": 50, "unit_price": 60.0}],
        auto_allocate=True
    )
    assert order_res2["order"].order_status == "BACKORDERED"
    assert order_res2["allocations"][0]["decision"] == "REJECTED"
