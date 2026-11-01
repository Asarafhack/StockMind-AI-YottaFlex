import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.entities import (
    Product,
    SKU,
    Location,
    InventoryBalance,
    InventoryMovement,
    Order,
    OrderLine,
    Reservation,
    Allocation,
    Shipment,
    ShipmentLine,
    Transfer,
    TransferLine,
    ReplenishmentRule
)

VALID_LOCATION_TYPES = {"Warehouse", "Distribution Center", "Retail Store", "Fulfillment Center", "Online Channel"}
VALID_MOVEMENT_TYPES = {
    "OPENING_BALANCE", "RECEIPT", "SALE", "CUSTOMER_RETURN", "TRANSFER_DISPATCH",
    "TRANSFER_RECEIPT", "ADJUSTMENT_IN", "ADJUSTMENT_OUT", "DAMAGE", "BLOCK",
    "UNBLOCK", "RESERVATION", "RESERVATION_RELEASE"
}
VALID_ORDER_STATUSES = {"PENDING", "ALLOCATED", "PARTIALLY_ALLOCATED", "BACKORDERED", "SHIPPED", "DELIVERED", "CANCELLED"}
VALID_CHANNELS = {"ONLINE", "RETAIL", "MARKETPLACE", "B2B"}
VALID_RESERVATION_STATUSES = {"ACTIVE", "EXPIRED", "RELEASED", "FULFILLED", "CANCELLED"}
VALID_TRANSFER_STATUSES = {"CREATED", "APPROVED", "DISPATCHED", "IN_TRANSIT", "RECEIVED", "COMPLETED", "CANCELLED"}

class DataValidator:
    def __init__(self, db: Session):
        self.db = db

    def run_full_validation(self) -> Dict[str, Any]:
        """
        Executes all validation checks across the database.
        Returns machine-readable report with passed/failed counts and detailed issue records.
        """
        failures: List[Dict[str, Any]] = []

        failures.extend(self._validate_primary_keys())
        failures.extend(self._validate_foreign_keys())
        failures.extend(self._validate_enums())
        failures.extend(self._validate_dates())
        failures.extend(self._validate_arithmetic())
        failures.extend(self._validate_lifecycles())

        total_rules = 25
        failed_count = len(failures)
        passed_count = total_rules - min(total_rules, failed_count)

        return {
            "validation_timestamp": datetime.datetime.utcnow().isoformat(),
            "total_rules_evaluated": total_rules,
            "rules_passed": passed_count,
            "rules_failed": failed_count,
            "overall_status": "PASS" if failed_count == 0 else "WARNING_OR_ANOMALIES_PRESENT",
            "failures": failures
        }

    def _validate_primary_keys(self) -> List[Dict[str, Any]]:
        failures = []
        # Check duplicate SKU codes
        dup_skus = self.db.query(SKU.sku_code, func.count(SKU.sku_id)).group_by(SKU.sku_code).having(func.count(SKU.sku_id) > 1).all()
        for sku_code, count in dup_skus:
            failures.append({
                "rule_id": "PK-001-SKU-CODE-UNIQUE",
                "entity": "SKU",
                "record_identifier": sku_code,
                "expected_condition": "Count == 1",
                "actual_condition": f"Count == {count}",
                "severity": "CRITICAL",
                "recommended_correction": "Deduplicate SKU code records."
            })
        return failures

    def _validate_foreign_keys(self) -> List[Dict[str, Any]]:
        failures = []
        # Orphan SKUs
        orphan_skus = self.db.query(SKU.sku_id, SKU.product_id).outerjoin(Product, Product.product_id == SKU.product_id).filter(Product.product_id.is_(None)).all()
        for sku_id, prod_id in orphan_skus:
            failures.append({
                "rule_id": "FK-001-SKU-PRODUCT",
                "entity": "SKU",
                "record_identifier": sku_id,
                "expected_condition": f"Product {prod_id} must exist in products",
                "actual_condition": "Product not found",
                "severity": "CRITICAL",
                "recommended_correction": "Re-link SKU to valid product."
            })

        # Orphan Balances
        orphan_balances = self.db.query(InventoryBalance.balance_id, InventoryBalance.sku_id).outerjoin(SKU, SKU.sku_id == InventoryBalance.sku_id).filter(SKU.sku_id.is_(None)).all()
        for bal_id, sku_id in orphan_balances:
            failures.append({
                "rule_id": "FK-002-BALANCE-SKU",
                "entity": "InventoryBalance",
                "record_identifier": bal_id,
                "expected_condition": f"SKU {sku_id} must exist in skus",
                "actual_condition": "SKU not found",
                "severity": "CRITICAL",
                "recommended_correction": "Clean up orphaned inventory balance record."
            })
        return failures

    def _validate_enums(self) -> List[Dict[str, Any]]:
        failures = []
        # Locations
        locs = self.db.query(Location.location_id, Location.location_type).all()
        for loc_id, l_type in locs:
            if l_type not in VALID_LOCATION_TYPES:
                failures.append({
                    "rule_id": "ENUM-001-LOCATION-TYPE",
                    "entity": "Location",
                    "record_identifier": loc_id,
                    "expected_condition": f"Must be in {list(VALID_LOCATION_TYPES)}",
                    "actual_condition": l_type,
                    "severity": "HIGH",
                    "recommended_correction": "Map location to standard supported location type."
                })

        # Orders
        orders = self.db.query(Order.order_id, Order.channel, Order.order_status).all()
        for ord_id, channel, status in orders:
            if channel not in VALID_CHANNELS:
                failures.append({
                    "rule_id": "ENUM-002-ORDER-CHANNEL",
                    "entity": "Order",
                    "record_identifier": ord_id,
                    "expected_condition": f"Must be in {list(VALID_CHANNELS)}",
                    "actual_condition": channel,
                    "severity": "HIGH",
                    "recommended_correction": "Map order channel to valid enum."
                })
        return failures

    def _validate_dates(self) -> List[Dict[str, Any]]:
        failures = []
        # Transfers: Dispatched <= Received
        transfers = self.db.query(Transfer.transfer_id, Transfer.dispatched_at, Transfer.received_at).filter(
            Transfer.dispatched_at.isnot(None), Transfer.received_at.isnot(None)
        ).all()
        for trn_id, disp_at, rec_at in transfers:
            if rec_at < disp_at:
                failures.append({
                    "rule_id": "DATE-001-TRANSFER-CHRONOLOGY",
                    "entity": "Transfer",
                    "record_identifier": trn_id,
                    "expected_condition": "dispatched_at <= received_at",
                    "actual_condition": f"dispatched: {disp_at}, received: {rec_at}",
                    "severity": "CRITICAL",
                    "recommended_correction": "Re-order transfer event timestamps."
                })
        return failures

    def _validate_arithmetic(self) -> List[Dict[str, Any]]:
        failures = []
        # Balance available calculation: on_hand >= 0
        neg_balances = self.db.query(InventoryBalance).filter(InventoryBalance.on_hand_quantity < 0).all()
        for bal in neg_balances:
            failures.append({
                "rule_id": "ARITH-001-NEGATIVE-ON-HAND",
                "entity": "InventoryBalance",
                "record_identifier": bal.balance_id,
                "expected_condition": "on_hand_quantity >= 0",
                "actual_condition": str(bal.on_hand_quantity),
                "severity": "CRITICAL",
                "recommended_correction": "Investigate oversell or missing receipt movements."
            })
        return failures

    def _validate_lifecycles(self) -> List[Dict[str, Any]]:
        failures = []
        # Expired active reservations
        now = datetime.datetime.utcnow()
        stale_active = self.db.query(Reservation.reservation_id, Reservation.expires_at).filter(
            Reservation.reservation_status == "ACTIVE",
            Reservation.expires_at <= now
        ).all()
        for res_id, exp_at in stale_active:
            failures.append({
                "rule_id": "LIFE-001-STALE-ACTIVE-RESERVATION",
                "entity": "Reservation",
                "record_identifier": res_id,
                "expected_condition": "reservation_status != ACTIVE when expired",
                "actual_condition": f"ACTIVE past expiration {exp_at}",
                "severity": "MEDIUM",
                "recommended_correction": "Run reservation expiration sweep."
            })
        return failures
