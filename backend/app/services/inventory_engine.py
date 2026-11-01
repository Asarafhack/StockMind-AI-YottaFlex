import datetime
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from backend.app.models.entities import (
    InventoryBalance,
    InventoryMovement,
    SKU,
    Location,
    AuditEvent
)

# Movement impact mapping on On-Hand stock
# Positive impact on location's on-hand
INBOUND_MOVEMENTS = {
    "OPENING_BALANCE",
    "RECEIPT",
    "CUSTOMER_RETURN",
    "TRANSFER_RECEIPT",
    "ADJUSTMENT_IN",
    "UNBLOCK"  # unblock restores blocked stock to available, keeps on-hand
}

# Negative impact on location's on-hand
OUTBOUND_MOVEMENTS = {
    "SALE",
    "TRANSFER_DISPATCH",
    "ADJUSTMENT_OUT",
    "DAMAGE"
}

class InventoryEngine:
    def __init__(self, db: Session):
        self.db = db

    def record_movement(
        self,
        sku_id: str,
        movement_type: str,
        quantity: int,
        reference_type: str,
        source_location_id: Optional[str] = None,
        destination_location_id: Optional[str] = None,
        reference_id: Optional[str] = None,
        transfer_id: Optional[str] = None,
        reason_code: Optional[str] = None,
        created_by: str = "SYSTEM",
        metadata_json: Optional[str] = None,
        occurred_at: Optional[datetime.datetime] = None,
        movement_id: Optional[str] = None,
    ) -> InventoryMovement:
        """
        Append-only movement recording. Updates derived InventoryBalance atomically.
        """
        now = datetime.datetime.utcnow()
        if occurred_at is None:
            occurred_at = now

        if not movement_id:
            # Deterministic/sequential format: MOV-YYYY-XXXXXXXX
            count = self.db.query(func.count(InventoryMovement.movement_id)).scalar() or 0
            year = occurred_at.year
            movement_id = f"MOV-{year}-{count + 1:08d}"

        movement = InventoryMovement(
            movement_id=movement_id,
            sku_id=sku_id,
            source_location_id=source_location_id,
            destination_location_id=destination_location_id,
            movement_type=movement_type,
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            transfer_id=transfer_id,
            occurred_at=occurred_at,
            recorded_at=now,
            reason_code=reason_code,
            created_by=created_by,
            metadata_json=metadata_json
        )
        self.db.add(movement)
        self.db.flush()

        # Update affected balances
        if destination_location_id:
            self._update_balance_from_movement(sku_id, destination_location_id, movement, is_destination=True)
        if source_location_id:
            self._update_balance_from_movement(sku_id, source_location_id, movement, is_destination=False)

        # Audit entry
        audit = AuditEvent(
            audit_id=f"AUD-{now.strftime('%Y%m%d%H%M%S%f')}",
            timestamp=now,
            event_type="INVENTORY_MOVEMENT",
            entity_type="InventoryMovement",
            entity_id=movement.movement_id,
            action=movement_type,
            user_id=created_by,
            details=f"Quantity: {quantity}, Sku: {sku_id}, Src: {source_location_id}, Dest: {destination_location_id}"
        )
        self.db.add(audit)
        self.db.commit()
        return movement

    def _get_or_create_balance(self, sku_id: str, location_id: str) -> InventoryBalance:
        balance = self.db.query(InventoryBalance).filter_by(sku_id=sku_id, location_id=location_id).first()
        if not balance:
            count = self.db.query(func.count(InventoryBalance.balance_id)).scalar() or 0
            balance = InventoryBalance(
                balance_id=f"BAL-{count + 1:06d}",
                sku_id=sku_id,
                location_id=location_id,
                on_hand_quantity=0,
                reserved_quantity=0,
                blocked_quantity=0,
                safety_stock_quantity=0,
                in_transit_quantity=0,
                available_quantity=0,
                version=1
            )
            self.db.add(balance)
            self.db.flush()
        return balance

    def _update_balance_from_movement(self, sku_id: str, location_id: str, movement: InventoryMovement, is_destination: bool):
        balance = self._get_or_create_balance(sku_id, location_id)
        qty = movement.quantity
        m_type = movement.movement_type

        if is_destination:
            if m_type in ["OPENING_BALANCE", "RECEIPT", "CUSTOMER_RETURN", "TRANSFER_RECEIPT", "ADJUSTMENT_IN"]:
                balance.on_hand_quantity += qty
            elif m_type == "BLOCK":
                balance.blocked_quantity += qty
            elif m_type == "UNBLOCK":
                balance.blocked_quantity = max(0, balance.blocked_quantity - qty)
        else: # is source
            if m_type in ["SALE", "TRANSFER_DISPATCH", "ADJUSTMENT_OUT", "DAMAGE"]:
                balance.on_hand_quantity = max(0, balance.on_hand_quantity - qty)
            elif m_type == "BLOCK":
                balance.blocked_quantity += qty
            elif m_type == "UNBLOCK":
                balance.blocked_quantity = max(0, balance.blocked_quantity - qty)

        # Re-derive available stock: on_hand - reserved - blocked
        balance.available_quantity = max(0, balance.on_hand_quantity - balance.reserved_quantity - balance.blocked_quantity)
        balance.last_movement_id = movement.movement_id
        balance.version += 1
        balance.updated_at = datetime.datetime.utcnow()
        self.db.flush()

    def calculate_ledger_on_hand(self, sku_id: str, location_id: str) -> int:
        """
        Independently calculates on-hand balance strictly from the immutable movement ledger.
        Formula:
          ON_HAND = Inbound movements - Outbound movements
        """
        # Sum of movements where location is destination (inbound)
        inbound_sum = self.db.query(func.coalesce(func.sum(InventoryMovement.quantity), 0)).filter(
            InventoryMovement.sku_id == sku_id,
            InventoryMovement.destination_location_id == location_id,
            InventoryMovement.movement_type.in_([
                "OPENING_BALANCE", "RECEIPT", "CUSTOMER_RETURN", "TRANSFER_RECEIPT", "ADJUSTMENT_IN"
            ])
        ).scalar() or 0

        # Sum of movements where location is source (outbound)
        outbound_sum = self.db.query(func.coalesce(func.sum(InventoryMovement.quantity), 0)).filter(
            InventoryMovement.sku_id == sku_id,
            InventoryMovement.source_location_id == location_id,
            InventoryMovement.movement_type.in_([
                "SALE", "TRANSFER_DISPATCH", "ADJUSTMENT_OUT", "DAMAGE"
            ])
        ).scalar() or 0

        return int(inbound_sum - outbound_sum)

    def reconcile_balance(self, sku_id: str, location_id: str) -> Dict[str, Any]:
        """
        Compares the derived/stored InventoryBalance against the ledger-calculated balance.
        """
        balance = self.db.query(InventoryBalance).filter_by(sku_id=sku_id, location_id=location_id).first()
        ledger_on_hand = self.calculate_ledger_on_hand(sku_id, location_id)
        stored_on_hand = balance.on_hand_quantity if balance else 0
        is_matched = (ledger_on_hand == stored_on_hand)
        discrepancy = stored_on_hand - ledger_on_hand

        return {
            "sku_id": sku_id,
            "location_id": location_id,
            "stored_on_hand": stored_on_hand,
            "ledger_on_hand": ledger_on_hand,
            "is_matched": is_matched,
            "discrepancy": discrepancy,
            "reconciliation_status": "MATCHED" if is_matched else "MISMATCH"
        }

    def record_compensating_adjustment(
        self,
        sku_id: str,
        location_id: str,
        reason: str,
        created_by: str = "RECONCILIATION_ENGINE"
    ) -> Optional[InventoryMovement]:
        """
        Applies a compensating movement to correct any ledger-to-physical inventory drift.
        Never modifies historical movements.
        """
        recon = self.reconcile_balance(sku_id, location_id)
        if recon["is_matched"]:
            return None

        discrepancy = recon["discrepancy"]
        if discrepancy < 0:
            # Stored is less than ledger or physical needs positive adjustment
            return self.record_movement(
                sku_id=sku_id,
                destination_location_id=location_id,
                movement_type="ADJUSTMENT_IN",
                quantity=abs(discrepancy),
                reference_type="RECONCILIATION_COMPENSATION",
                reason_code="RECONCILIATION_ADJUSTMENT",
                created_by=created_by,
                metadata_json=f'{{"reason": "{reason}", "discrepancy": {discrepancy}}}'
            )
        else:
            return self.record_movement(
                sku_id=sku_id,
                source_location_id=location_id,
                movement_type="ADJUSTMENT_OUT",
                quantity=discrepancy,
                reference_type="RECONCILIATION_COMPENSATION",
                reason_code="RECONCILIATION_ADJUSTMENT",
                created_by=created_by,
                metadata_json=f'{{"reason": "{reason}", "discrepancy": {discrepancy}}}'
            )
