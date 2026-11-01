import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Numeric, Float, Boolean, DateTime,
    ForeignKey, UniqueConstraint, Index, Text, Enum
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Product(Base):
    __tablename__ = "products"

    product_id = Column(String(32), primary_key=True)  # e.g., PRD-000001
    product_name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    brand = Column(String(128), nullable=False, index=True)
    category = Column(String(128), nullable=False, index=True)
    product_status = Column(String(32), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    skus = relationship("SKU", back_populates="product", cascade="all, delete-orphan")


class SKU(Base):
    __tablename__ = "skus"

    sku_id = Column(String(32), primary_key=True)  # e.g., SKU-000001
    product_id = Column(String(32), ForeignKey("products.product_id"), nullable=False, index=True)
    sku_code = Column(String(64), unique=True, nullable=False, index=True)
    barcode = Column(String(64), unique=True, nullable=True, index=True)
    variant = Column(String(128), nullable=False)
    unit_of_measure = Column(String(32), nullable=False, default="EACH")
    unit_cost = Column(Numeric(12, 2), nullable=False, default=0.0)
    selling_price = Column(Numeric(12, 2), nullable=False, default=0.0)
    weight = Column(Float, nullable=True)
    status = Column(String(32), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="skus")
    balances = relationship("InventoryBalance", back_populates="sku")
    replenishment_rules = relationship("ReplenishmentRule", back_populates="sku")


class Location(Base):
    __tablename__ = "locations"

    location_id = Column(String(32), primary_key=True)  # e.g., LOC-000001
    location_code = Column(String(64), unique=True, nullable=False, index=True)
    location_name = Column(String(255), nullable=False)
    location_type = Column(String(64), nullable=False, index=True)  # Warehouse, Distribution Center, Retail Store, Fulfillment Center, Online Channel
    parent_location_id = Column(String(32), ForeignKey("locations.location_id"), nullable=True)
    address = Column(String(255), nullable=False)
    city = Column(String(128), nullable=False, index=True)
    region = Column(String(128), nullable=False)
    country = Column(String(64), nullable=False, default="USA")
    timezone = Column(String(64), nullable=False, default="UTC")
    active_status = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    # Relationships
    parent_location = relationship("Location", remote_side=[location_id], backref="child_locations")
    balances = relationship("InventoryBalance", back_populates="location")
    replenishment_rules = relationship("ReplenishmentRule", back_populates="location")


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"

    balance_id = Column(String(32), primary_key=True)  # e.g., BAL-000001
    sku_id = Column(String(32), ForeignKey("skus.sku_id"), nullable=False, index=True)
    location_id = Column(String(32), ForeignKey("locations.location_id"), nullable=False, index=True)
    on_hand_quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, nullable=False, default=0)
    blocked_quantity = Column(Integer, nullable=False, default=0)
    safety_stock_quantity = Column(Integer, nullable=False, default=0)
    in_transit_quantity = Column(Integer, nullable=False, default=0)
    available_quantity = Column(Integer, nullable=False, default=0)
    last_movement_id = Column(String(32), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    sku = relationship("SKU", back_populates="balances")
    location = relationship("Location", back_populates="balances")

    __table_args__ = (
        UniqueConstraint("sku_id", "location_id", name="uq_sku_location"),
        Index("idx_balance_sku_loc", "sku_id", "location_id"),
    )


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    movement_id = Column(String(32), primary_key=True)  # e.g., MOV-2026-00000001
    sku_id = Column(String(32), ForeignKey("skus.sku_id"), nullable=False, index=True)
    source_location_id = Column(String(32), ForeignKey("locations.location_id"), nullable=True, index=True)
    destination_location_id = Column(String(32), ForeignKey("locations.location_id"), nullable=True, index=True)
    movement_type = Column(String(64), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    reference_type = Column(String(64), nullable=False)  # ORDER, TRANSFER, ADJUSTMENT, OPENING, PO, RETURN
    reference_id = Column(String(64), nullable=True, index=True)
    transfer_id = Column(String(32), nullable=True, index=True)
    occurred_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    recorded_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    reason_code = Column(String(64), nullable=True)
    created_by = Column(String(64), nullable=False, default="SYSTEM")
    metadata_json = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_mov_sku_dest", "sku_id", "destination_location_id"),
        Index("idx_mov_sku_src", "sku_id", "source_location_id"),
    )


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String(32), primary_key=True)  # e.g., ORD-2026-000001
    channel = Column(String(32), nullable=False, index=True)  # ONLINE, RETAIL, MARKETPLACE, B2B
    customer_reference = Column(String(64), nullable=False)  # Synthetic ID
    order_status = Column(String(32), nullable=False, default="PENDING", index=True)
    order_date = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    requested_delivery_date = Column(DateTime, nullable=True)
    fulfillment_location_id = Column(String(32), ForeignKey("locations.location_id"), nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    currency = Column(String(8), nullable=False, default="USD")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    # Relationships
    order_lines = relationship("OrderLine", back_populates="order", cascade="all, delete-orphan")
    fulfillment_location = relationship("Location", foreign_keys=[fulfillment_location_id])
    reservations = relationship("Reservation", back_populates="order")
    shipments = relationship("Shipment", back_populates="order")


class OrderLine(Base):
    __tablename__ = "order_lines"

    order_line_id = Column(String(32), primary_key=True)  # e.g., ORDL-2026-000001-01
    order_id = Column(String(32), ForeignKey("orders.order_id"), nullable=False, index=True)
    sku_id = Column(String(32), ForeignKey("skus.sku_id"), nullable=False, index=True)
    ordered_quantity = Column(Integer, nullable=False)
    allocated_quantity = Column(Integer, nullable=False, default=0)
    fulfilled_quantity = Column(Integer, nullable=False, default=0)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0.0)
    line_status = Column(String(32), nullable=False, default="PENDING")

    # Relationships
    order = relationship("Order", back_populates="order_lines")
    sku = relationship("SKU")
    reservations = relationship("Reservation", back_populates="order_line")
    allocations = relationship("Allocation", back_populates="order_line")


class Reservation(Base):
    __tablename__ = "reservations"

    reservation_id = Column(String(64), primary_key=True)  # e.g., RES-ORD-2026-000001-01
    order_id = Column(String(32), ForeignKey("orders.order_id"), nullable=False, index=True)
    order_line_id = Column(String(32), ForeignKey("order_lines.order_line_id"), nullable=False, index=True)
    sku_id = Column(String(32), ForeignKey("skus.sku_id"), nullable=False, index=True)
    location_id = Column(String(32), ForeignKey("locations.location_id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    reservation_status = Column(String(32), nullable=False, default="ACTIVE", index=True)  # ACTIVE, EXPIRED, RELEASED, FULFILLED, CANCELLED
    reserved_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    released_at = Column(DateTime, nullable=True)
    fulfilled_at = Column(DateTime, nullable=True)
    release_reason = Column(String(128), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="reservations")
    order_line = relationship("OrderLine", back_populates="reservations")
    sku = relationship("SKU")
    location = relationship("Location")

    __table_args__ = (
        Index("idx_res_status_exp", "reservation_status", "expires_at"),
        Index("idx_res_sku_loc_status", "sku_id", "location_id", "reservation_status"),
    )


class Allocation(Base):
    __tablename__ = "allocations"

    allocation_id = Column(String(32), primary_key=True)  # e.g., ALC-2026-000001
    order_line_id = Column(String(32), ForeignKey("order_lines.order_line_id"), nullable=False, index=True)
    sku_id = Column(String(32), ForeignKey("skus.sku_id"), nullable=False, index=True)
    location_id = Column(String(32), ForeignKey("locations.location_id"), nullable=False, index=True)
    reservation_id = Column(String(64), ForeignKey("reservations.reservation_id"), nullable=True)
    allocated_quantity = Column(Integer, nullable=False)
    decision = Column(String(32), nullable=False)  # ACCEPTED, REJECTED, PARTIAL
    decision_reason = Column(Text, nullable=False)
    allocated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    # Relationships
    order_line = relationship("OrderLine", back_populates="allocations")
    sku = relationship("SKU")
    location = relationship("Location")
    reservation = relationship("Reservation")


class Shipment(Base):
    __tablename__ = "shipments"

    shipment_id = Column(String(32), primary_key=True)  # e.g., SHP-2026-000001
    order_id = Column(String(32), ForeignKey("orders.order_id"), nullable=False, index=True)
    origin_location_id = Column(String(32), ForeignKey("locations.location_id"), nullable=False)
    destination_location_id = Column(String(32), ForeignKey("locations.location_id"), nullable=True)
    shipment_status = Column(String(32), nullable=False, default="PENDING", index=True)  # PENDING, SHIPPED, IN_TRANSIT, DELIVERED, CANCELLED
    carrier = Column(String(64), nullable=False)
    tracking_reference = Column(String(128), nullable=False, index=True)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="shipments")
    origin_location = relationship("Location", foreign_keys=[origin_location_id])
    destination_location = relationship("Location", foreign_keys=[destination_location_id])
    shipment_lines = relationship("ShipmentLine", back_populates="shipment", cascade="all, delete-orphan")


class ShipmentLine(Base):
    __tablename__ = "shipment_lines"

    shipment_line_id = Column(String(32), primary_key=True)
    shipment_id = Column(String(32), ForeignKey("shipments.shipment_id"), nullable=False, index=True)
    order_line_id = Column(String(32), ForeignKey("order_lines.order_line_id"), nullable=False)
    sku_id = Column(String(32), ForeignKey("skus.sku_id"), nullable=False)
    quantity = Column(Integer, nullable=False)

    shipment = relationship("Shipment", back_populates="shipment_lines")
    order_line = relationship("OrderLine")
    sku = relationship("SKU")


class Transfer(Base):
    __tablename__ = "transfers"

    transfer_id = Column(String(32), primary_key=True)  # e.g., TRN-2026-000001
    transfer_number = Column(String(64), unique=True, nullable=False, index=True)
    source_location_id = Column(String(32), ForeignKey("locations.location_id"), nullable=False, index=True)
    destination_location_id = Column(String(32), ForeignKey("locations.location_id"), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="CREATED", index=True)  # CREATED, APPROVED, DISPATCHED, IN_TRANSIT, RECEIVED, COMPLETED, CANCELLED
    requested_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    dispatched_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    carrier = Column(String(64), nullable=True)
    tracking_reference = Column(String(128), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    source_location = relationship("Location", foreign_keys=[source_location_id])
    destination_location = relationship("Location", foreign_keys=[destination_location_id])
    transfer_lines = relationship("TransferLine", back_populates="transfer", cascade="all, delete-orphan")


class TransferLine(Base):
    __tablename__ = "transfer_lines"

    transfer_line_id = Column(String(32), primary_key=True)
    transfer_id = Column(String(32), ForeignKey("transfers.transfer_id"), nullable=False, index=True)
    sku_id = Column(String(32), ForeignKey("skus.sku_id"), nullable=False, index=True)
    requested_quantity = Column(Integer, nullable=False)
    dispatched_quantity = Column(Integer, nullable=False, default=0)
    received_quantity = Column(Integer, nullable=False, default=0)

    transfer = relationship("Transfer", back_populates="transfer_lines")
    sku = relationship("SKU")


class ReplenishmentRule(Base):
    __tablename__ = "replenishment_rules"

    rule_id = Column(String(32), primary_key=True)  # e.g., RPL-000001
    sku_id = Column(String(32), ForeignKey("skus.sku_id"), nullable=False, index=True)
    location_id = Column(String(32), ForeignKey("locations.location_id"), nullable=False, index=True)
    minimum_stock = Column(Integer, nullable=False, default=10)
    maximum_stock = Column(Integer, nullable=False, default=100)
    reorder_point = Column(Integer, nullable=False, default=25)
    safety_stock = Column(Integer, nullable=False, default=15)
    lead_time_days = Column(Integer, nullable=False, default=5)
    reorder_quantity = Column(Integer, nullable=False, default=50)
    inbound_eligibility_policy = Column(String(64), nullable=False, default="ALLOW_CONFIRMED_IN_TRANSIT")
    effective_from = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    effective_to = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    sku = relationship("SKU", back_populates="replenishment_rules")
    location = relationship("Location", back_populates="replenishment_rules")

    __table_args__ = (
        UniqueConstraint("sku_id", "location_id", name="uq_rule_sku_loc"),
    )


class AnomalyRecord(Base):
    __tablename__ = "anomalies"

    anomaly_id = Column(String(32), primary_key=True)  # e.g., ANOM-2026-000001
    issue_type = Column(String(64), nullable=False, index=True)  # BALANCE_MISMATCH, RESERVATION_OVERFLOW, BLOCKED_STOCK_FULFILLMENT, PREMATURE_TRANSFER
    entity_type = Column(String(64), nullable=False)  # InventoryBalance, Reservation, OrderLine, Transfer
    entity_id = Column(String(64), nullable=False, index=True)
    affected_sku = Column(String(32), nullable=True, index=True)
    affected_location = Column(String(32), nullable=True, index=True)
    detection_timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    expected_value = Column(String(255), nullable=False)
    observed_value = Column(String(255), nullable=False)
    severity = Column(String(32), nullable=False, default="MEDIUM", index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    explanation = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    ground_truth_label = Column(String(64), nullable=True)  # e.g., INJECTED_ANOMALY, BENIGN
    status = Column(String(32), nullable=False, default="OPEN", index=True)  # OPEN, ACKNOWLEDGED, RESOLVED
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(64), nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    audit_id = Column(String(32), primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)
    user_id = Column(String(64), nullable=False, default="SYSTEM")
    details = Column(Text, nullable=True)
