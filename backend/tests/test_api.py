import pytest
from backend.app.api.products import get_products, create_product
from backend.app.api.skus import get_skus, create_sku
from backend.app.api.locations import get_locations, create_location
from backend.app.api.inventory import get_inventory_balances, get_sku_location_atp
from backend.app.api.analytics import get_analytics_overview, simulate_what_if_scenario
from backend.app.schemas.schemas import ProductCreate, SKUCreate, LocationCreate
from backend.app.models.entities import Product, SKU, Location, InventoryBalance
from decimal import Decimal

def test_api_products_crud(db_session):
    p_in = ProductCreate(
        product_name="Pro Monitor 27",
        brand="Apex",
        category="Electronics",
        product_status="ACTIVE"
    )
    created = create_product(p_in, db=db_session)
    assert created.product_name == "Pro Monitor 27"
    assert created.product_id.startswith("PRD-")

    prods = get_products(category="Electronics", skip=0, limit=10, db=db_session)
    assert len(prods) == 1
    assert prods[0].product_id == created.product_id

def test_api_skus_crud(db_session):
    p_in = ProductCreate(product_name="Laptop Pro", brand="Apex", category="Electronics")
    prod = create_product(p_in, db=db_session)

    sku_in = SKUCreate(
        product_id=prod.product_id,
        sku_code="SKU-APX-LAP-01",
        variant="16GB / 512GB",
        unit_cost=Decimal("600.00"),
        selling_price=Decimal("999.00")
    )
    created_sku = create_sku(sku_in, db=db_session)
    assert created_sku.sku_code == "SKU-APX-LAP-01"

    skus = get_skus(product_id=prod.product_id, skip=0, limit=10, db=db_session)
    assert len(skus) == 1
    assert skus[0].sku_id == created_sku.sku_id

def test_api_locations_crud(db_session):
    loc_in = LocationCreate(
        location_code="LC-TEST-99",
        location_name="Dallas Central Hub",
        location_type="Distribution Center",
        address="100 Logistics Way",
        city="Dallas",
        region="TX",
        country="USA"
    )
    created_loc = create_location(loc_in, db=db_session)
    assert created_loc.location_code == "LC-TEST-99"

    locs = get_locations(city="Dallas", skip=0, limit=10, db=db_session)
    assert len(locs) == 1
    assert locs[0].location_id == created_loc.location_id

def test_api_inventory_and_atp(db_session):
    # Setup SKU & Location
    prod = Product(product_id="PRD-API-01", product_name="Test", brand="Apex", category="Tools")
    loc = Location(location_id="LOC-API-01", location_code="LC-API-01", location_name="Hub", location_type="Warehouse", address="1", city="A", region="B")
    sku = SKU(sku_id="SKU-API-01", product_id="PRD-API-01", sku_code="SKU-A-01", variant="Std", unit_cost=10, selling_price=20)
    bal = InventoryBalance(
        balance_id="BAL-API-01",
        sku_id="SKU-API-01",
        location_id="LOC-API-01",
        on_hand_quantity=100,
        reserved_quantity=20,
        blocked_quantity=10,
        safety_stock_quantity=15,
        available_quantity=70,
        version=1
    )
    db_session.add_all([prod, loc, sku, bal])
    db_session.commit()

    # Query inventory
    inventory_items = get_inventory_balances(sku_id="SKU-API-01", db=db_session)
    assert len(inventory_items) == 1
    assert inventory_items[0].on_hand_quantity == 100

    # Query ATP
    atp_res = get_sku_location_atp("SKU-API-01", "LOC-API-01", db=db_session)
    assert atp_res.on_hand_stock == 100
    assert atp_res.reserved_stock == 0  # No active reservation records
    assert atp_res.blocked_stock == 10
    assert atp_res.final_atp == 90

def test_api_analytics_overview_and_what_if(db_session):
    overview = get_analytics_overview(db=db_session)
    assert overview.total_skus >= 0
    assert overview.fulfillment_rate_pct >= 0.0

    simulation = simulate_what_if_scenario(demand_surge_pct=30.0, lead_time_delay_days=7, db=db_session)
    assert simulation["scenario_parameters"]["demand_surge_pct"] == 30.0
    assert "projected_simulation" in simulation
