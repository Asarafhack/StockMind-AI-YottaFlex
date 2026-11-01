import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.entities import (
    Transfer,
    TransferLine,
    InventoryBalance,
    AuditEvent
)
from backend.app.services.inventory_engine import InventoryEngine

class TransferEngine:
    def __init__(self, db: Session):
        self.db = db
        self.inventory_engine = InventoryEngine(db)

    def create_transfer(
        self,
        source_location_id: str,
        destination_location_id: str,
        lines: List[Dict[str, Any]],
        carrier: Optional[str] = None,
        tracking_reference: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Transfer:
        """
        Creates a transfer in CREATED status.
        """
        now = datetime.datetime.utcnow()
        count = self.db.query(func.count(Transfer.transfer_id)).scalar() or 0
        year = now.year
        transfer_id = f"TRN-{year}-{count + 1:06d}"
        transfer_number = f"TRN-NO-{year}-{count + 1:06d}"

        transfer = Transfer(
            transfer_id=transfer_id,
            transfer_number=transfer_number,
            source_location_id=source_location_id,
            destination_location_id=destination_location_id,
            status="CREATED",
            requested_at=now,
            carrier=carrier,
            tracking_reference=tracking_reference,
            notes=notes
        )
        self.db.add(transfer)
        self.db.flush()

        for idx, line in enumerate(lines, start=1):
            tl_id = f"TRNL-{transfer_id}-{idx:02d}"
            t_line = TransferLine(
                transfer_line_id=tl_id,
                transfer_id=transfer_id,
                sku_id=line["sku_id"],
                requested_quantity=line["requested_quantity"],
                dispatched_quantity=0,
                received_quantity=0
            )
            self.db.add(t_line)

        self.db.commit()
        return transfer

    def approve_transfer(self, transfer_id: str) -> Dict[str, Any]:
        transfer = self.db.query(Transfer).filter_by(transfer_id=transfer_id).first()
        if not transfer:
            return {"success": False, "error": f"Transfer {transfer_id} not found"}
        if transfer.status != "CREATED":
            return {"success": False, "error": f"Transfer in status {transfer.status} cannot be approved"}

        transfer.status = "APPROVED"
        self.db.commit()
        return {"success": True, "transfer": transfer}

    def dispatch_transfer(
        self,
        transfer_id: str,
        carrier: Optional[str] = None,
        tracking_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dispatches transfer:
        - Reduces source on-hand stock.
        - Records TRANSFER_DISPATCH movement.
        - Increments in_transit_quantity at destination balance.
        - Status becomes IN_TRANSIT.
        """
        now = datetime.datetime.utcnow()
        transfer = self.db.query(Transfer).filter_by(transfer_id=transfer_id).first()
        if not transfer:
            return {"success": False, "error": f"Transfer {transfer_id} not found"}
        if transfer.status not in ["CREATED", "APPROVED"]:
            return {"success": False, "error": f"Transfer in status {transfer.status} cannot be dispatched"}

        if carrier:
            transfer.carrier = carrier
        if tracking_reference:
            transfer.tracking_reference = tracking_reference

        transfer.status = "IN_TRANSIT"
        transfer.dispatched_at = now

        for line in transfer.transfer_lines:
            dispatch_qty = line.requested_quantity
            line.dispatched_quantity = dispatch_qty

            # 1. Outbound movement from source
            self.inventory_engine.record_movement(
                sku_id=line.sku_id,
                source_location_id=transfer.source_location_id,
                destination_location_id=None,
                movement_type="TRANSFER_DISPATCH",
                quantity=dispatch_qty,
                reference_type="INTER_LOCATION_TRANSFER",
                reference_id=transfer.transfer_id,
                transfer_id=transfer.transfer_id,
                reason_code="TRANSFER_OUTBOUND",
                created_by="TRANSFER_ENGINE",
                occurred_at=now
            )

            # 2. Increment in-transit at destination balance (do NOT add to on_hand yet!)
            dest_bal = self.inventory_engine._get_or_create_balance(line.sku_id, transfer.destination_location_id)
            dest_bal.in_transit_quantity += dispatch_qty
            dest_bal.updated_at = now

        self.db.commit()
        return {"success": True, "transfer": transfer}

    def receive_transfer(self, transfer_id: str) -> Dict[str, Any]:
        """
        Receives transfer:
        - Decrements in_transit_quantity at destination balance.
        - Increments on_hand_quantity at destination balance.
        - Records TRANSFER_RECEIPT movement.
        - Status becomes COMPLETED.
        """
        now = datetime.datetime.utcnow()
        transfer = self.db.query(Transfer).filter_by(transfer_id=transfer_id).first()
        if not transfer:
            return {"success": False, "error": f"Transfer {transfer_id} not found"}
        if transfer.status != "IN_TRANSIT":
            return {"success": False, "error": f"Transfer in status {transfer.status} cannot be received directly"}

        transfer.status = "COMPLETED"
        transfer.received_at = now

        for line in transfer.transfer_lines:
            received_qty = line.dispatched_quantity
            line.received_quantity = received_qty

            # 1. Decrement in-transit at destination
            dest_bal = self.inventory_engine._get_or_create_balance(line.sku_id, transfer.destination_location_id)
            dest_bal.in_transit_quantity = max(0, dest_bal.in_transit_quantity - received_qty)

            # 2. Inbound movement at destination (increments on_hand)
            self.inventory_engine.record_movement(
                sku_id=line.sku_id,
                source_location_id=None,
                destination_location_id=transfer.destination_location_id,
                movement_type="TRANSFER_RECEIPT",
                quantity=received_qty,
                reference_type="INTER_LOCATION_TRANSFER",
                reference_id=transfer.transfer_id,
                transfer_id=transfer.transfer_id,
                reason_code="TRANSFER_INBOUND",
                created_by="TRANSFER_ENGINE",
                occurred_at=now
            )

        self.db.commit()
        return {"success": True, "transfer": transfer}

    def cancel_transfer(self, transfer_id: str, reason: str = "CANCELLED_BY_OPERATOR") -> Dict[str, Any]:
        """
        Cancels transfer before dispatch.
        """
        transfer = self.db.query(Transfer).filter_by(transfer_id=transfer_id).first()
        if not transfer:
            return {"success": False, "error": f"Transfer {transfer_id} not found"}
        if transfer.status in ["DISPATCHED", "IN_TRANSIT", "COMPLETED"]:
            return {"success": False, "error": f"Cannot cancel transfer already in status {transfer.status}"}

        transfer.status = "CANCELLED"
        transfer.notes = f"{transfer.notes or ''} [Cancelled: {reason}]"
        self.db.commit()
        return {"success": True, "transfer": transfer}
