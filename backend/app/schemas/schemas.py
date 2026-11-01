from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

# Base Schema
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# Product Schemas
class ProductBase(BaseSchema):
    product_name: str
    description: Optional[str] = None
    brand: str
    category: str
    product_status: str = "ACTIVE"

class ProductCreate(ProductBase):
    product_id: Optional[str] = None

class ProductResponse(ProductBase):
    product_id: str
    created_at: datetime
    updated_at: datetime

# SKU Schemas
class SKUBase(BaseSchema):
    product_id: str
    sku_code: str
    barcode: Optional[str] = None
    variant: str
    unit_of_measure: str = "EACH"
    unit_cost: Decimal
    selling_price: Decimal
    weight: Optional[float] = None
    status: str = "ACTIVE"

class SKUCreate(SKUBase):
    sku_id: Optional[str] = None

class SKUResponse(SKUBase):
    sku_id: str
    created_at: datetime

# Location Schemas
class LocationBase(BaseSchema):
    location_code: str
    location_name: str
    location_type: str
    parent_location_id: Optional[str] = None
    address: str
    city: str
    region: str
    country: str = "USA"
    timezone: str = "UTC"
    active_status: bool = True

class LocationCreate(LocationBase):
    location_id: Optional[str] = None

class LocationResponse(LocationBase):
    location_id: str
    created_at: datetime

# Inventory Balance Schemas
class InventoryBalanceResponse(BaseSchema):
    balance_id: str
    sku_id: str
    location_id: str
    on_hand_quantity: int
    reserved_quantity: int
    blocked_quantity: int
    safety_stock_quantity: int
    in_transit_quantity: int
    available_quantity: int
    last_movement_id: Optional[str] = None
    version: int
    updated_at: datetime

# Inventory Movement Schemas
class InventoryMovementCreate(BaseSchema):
    sku_id: str
    source_location_id: Optional[str] = None
    destination_location_id: Optional[str] = None
    movement_type: str
    quantity: int
    reference_type: str
    reference_id: Optional[str] = None
    transfer_id: Optional[str] = None
    reason_code: Optional[str] = None
    created_by: str = "SYSTEM"
    metadata_json: Optional[str] = None

class InventoryMovementResponse(BaseSchema):
    movement_id: str
    sku_id: str
    source_location_id: Optional[str] = None
    destination_location_id: Optional[str] = None
    movement_type: str
    quantity: int
    reference_type: str
    reference_id: Optional[str] = None
    transfer_id: Optional[str] = None
    occurred_at: datetime
    recorded_at: datetime
    reason_code: Optional[str] = None
    created_by: str
    metadata_json: Optional[str] = None

# ATP Breakdown Response (Part 7 non-negotiable requirement)
class ATPResponse(BaseSchema):
    sku_id: str
    location_id: str
    on_hand_stock: int
    reserved_stock: int
    blocked_stock: int
    safety_stock: int
    eligible_inbound: int
    final_atp: int
    reservable_stock: int
    calculation_timestamp: datetime
    source_movement_references: List[str] = []
    explanatory_decision_reason: str

# Reservation Schemas
class ReservationCreate(BaseSchema):
    order_id: str
    order_line_id: str
    sku_id: str
    location_id: str
    quantity: int
    duration_minutes: int = 60

class ReservationResponse(BaseSchema):
    reservation_id: str
    order_id: str
    order_line_id: str
    sku_id: str
    location_id: str
    quantity: int
    reservation_status: str
    reserved_at: datetime
    expires_at: datetime
    released_at: Optional[datetime] = None
    fulfilled_at: Optional[datetime] = None
    release_reason: Optional[str] = None

# Order & OrderLine Schemas
class OrderLineCreate(BaseSchema):
    sku_id: str
    ordered_quantity: int
    unit_price: Decimal

class OrderLineResponse(BaseSchema):
    order_line_id: str
    order_id: str
    sku_id: str
    ordered_quantity: int
    allocated_quantity: int
    fulfilled_quantity: int
    unit_price: Decimal
    line_status: str

class OrderCreate(BaseSchema):
    channel: str = "ONLINE"
    customer_reference: str
    requested_delivery_date: Optional[datetime] = None
    lines: List[OrderLineCreate]

class OrderResponse(BaseSchema):
    order_id: str
    channel: str
    customer_reference: str
    order_status: str
    order_date: datetime
    requested_delivery_date: Optional[datetime] = None
    fulfillment_location_id: Optional[str] = None
    total_amount: Decimal
    currency: str
    created_at: datetime
    order_lines: List[OrderLineResponse] = []

# Order Allocation Decision
class AllocationDecisionResponse(BaseSchema):
    allocation_id: str
    order_line_id: str
    sku_id: str
    location_id: str
    requested_quantity: int
    allocated_quantity: int
    available_stock_at_decision: int
    decision: str  # ACCEPTED, REJECTED, PARTIAL
    decision_reason: str
    reservation_id: Optional[str] = None
    allocated_at: datetime

# Shipment Schemas
class ShipmentLineResponse(BaseSchema):
    shipment_line_id: str
    shipment_id: str
    order_line_id: str
    sku_id: str
    quantity: int

class ShipmentResponse(BaseSchema):
    shipment_id: str
    order_id: str
    origin_location_id: str
    destination_location_id: Optional[str] = None
    shipment_status: str
    carrier: str
    tracking_reference: str
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    shipment_lines: List[ShipmentLineResponse] = []

# Transfer Schemas
class TransferLineCreate(BaseSchema):
    sku_id: str
    requested_quantity: int

class TransferLineResponse(BaseSchema):
    transfer_line_id: str
    transfer_id: str
    sku_id: str
    requested_quantity: int
    dispatched_quantity: int
    received_quantity: int

class TransferCreate(BaseSchema):
    source_location_id: str
    destination_location_id: str
    carrier: Optional[str] = None
    tracking_reference: Optional[str] = None
    notes: Optional[str] = None
    lines: List[TransferLineCreate]

class TransferResponse(BaseSchema):
    transfer_id: str
    transfer_number: str
    source_location_id: str
    destination_location_id: str
    status: str
    requested_at: datetime
    dispatched_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    carrier: Optional[str] = None
    tracking_reference: Optional[str] = None
    notes: Optional[str] = None
    transfer_lines: List[TransferLineResponse] = []

# Replenishment Rule Schemas
class ReplenishmentRuleResponse(BaseSchema):
    rule_id: str
    sku_id: str
    location_id: str
    minimum_stock: int
    maximum_stock: int
    reorder_point: int
    safety_stock: int
    lead_time_days: int
    reorder_quantity: int
    inbound_eligibility_policy: str
    effective_from: datetime
    effective_to: Optional[datetime] = None
    is_active: bool

# Anomaly Record Schemas
class AnomalyResponse(BaseSchema):
    anomaly_id: str
    issue_type: str
    entity_type: str
    entity_id: str
    affected_sku: Optional[str] = None
    affected_location: Optional[str] = None
    detection_timestamp: datetime
    expected_value: str
    observed_value: str
    severity: str
    explanation: str
    recommended_action: str
    ground_truth_label: Optional[str] = None
    status: str
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

# Analytics & KPI Overview Schemas
class KPIOverview(BaseSchema):
    total_skus: int
    total_locations: int
    total_on_hand_inventory: int
    available_to_promise_quantity: int
    active_reservations: int
    in_transit_inventory: int
    open_orders: int
    fulfillment_rate_pct: float
    inventory_accuracy_pct: float
    total_anomalies: int
    critical_anomalies: int
    open_anomalies: int
    stockout_rate_pct: float
    reservation_expiry_rate_pct: float

# Generator Job Schemas
class GeneratorJobRequest(BaseSchema):
    profile: str = "starter"  # starter or full
    seed: int = 20261022
    batch_size: int = 1000
    include_anomalies: bool = True
    output_formats: List[str] = ["csv", "json", "parquet", "sql"]

class GeneratorJobResponse(BaseSchema):
    job_id: str
    status: str
    profile: str
    seed: int
    records_generated: Dict[str, int] = {}
    progress_pct: float = 0.0
    elapsed_seconds: float = 0.0
    estimated_remaining_seconds: float = 0.0
    manifest_path: Optional[str] = None
    checksum_verified: bool = False
    message: str = ""
