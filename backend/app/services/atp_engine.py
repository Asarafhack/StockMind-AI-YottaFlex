import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.entities import (
    InventoryBalance,
    InventoryMovement,
    Reservation,
    ReplenishmentRule,
    Transfer,
    TransferLine
)
from backend.app.schemas.schemas import ATPResponse

class ATPEngine:
    def __init__(self, db: Session):
        self.db = db

    def calculate_atp(
        self,
        sku_id: str,
        location_id: str,
        protect_safety_stock_in_atp: bool = False
    ) -> ATPResponse:
        """
        Calculates Available-to-Promise (ATP) and Reservable Stock deterministically.
        Formula:
          ATP = ON_HAND - ACTIVE_RESERVATIONS - BLOCKED_STOCK + ELIGIBLE_INBOUND
          RESERVABLE_STOCK = ON_HAND - BLOCKED_STOCK - ACTIVE_RESERVATIONS - SAFETY_STOCK
        """
        now = datetime.datetime.utcnow()

        # 1. Fetch balance
        balance = self.db.query(InventoryBalance).filter_by(
            sku_id=sku_id, location_id=location_id
        ).first()

        on_hand = balance.on_hand_quantity if balance else 0
        blocked = balance.blocked_quantity if balance else 0

        # 2. Fetch active reservations (only non-expired, non-released)
        active_reservations = self.db.query(func.coalesce(func.sum(Reservation.quantity), 0)).filter(
            Reservation.sku_id == sku_id,
            Reservation.location_id == location_id,
            Reservation.reservation_status == "ACTIVE",
            Reservation.expires_at > now
        ).scalar() or 0

        # 3. Fetch replenishment rule & safety stock
        rule = self.db.query(ReplenishmentRule).filter_by(
            sku_id=sku_id, location_id=location_id, is_active=True
        ).first()

        safety_stock = rule.safety_stock if rule else (balance.safety_stock_quantity if balance else 0)
        inbound_policy = rule.inbound_eligibility_policy if rule else "ALLOW_CONFIRMED_IN_TRANSIT"

        # 4. Calculate eligible inbound stock based on policy
        eligible_inbound = 0
        if inbound_policy == "ALLOW_CONFIRMED_IN_TRANSIT":
            # Transfers in status 'IN_TRANSIT' with tracking
            inbound_query = self.db.query(func.coalesce(func.sum(TransferLine.dispatched_quantity - TransferLine.received_quantity), 0))\
                .join(Transfer, Transfer.transfer_id == TransferLine.transfer_id)\
                .filter(
                    Transfer.destination_location_id == location_id,
                    TransferLine.sku_id == sku_id,
                    Transfer.status == "IN_TRANSIT",
                    Transfer.tracking_reference.isnot(None)
                )
            eligible_inbound = inbound_query.scalar() or 0
        elif inbound_policy == "ALLOW_ALL_IN_TRANSIT":
            inbound_query = self.db.query(func.coalesce(func.sum(TransferLine.dispatched_quantity - TransferLine.received_quantity), 0))\
                .join(Transfer, Transfer.transfer_id == TransferLine.transfer_id)\
                .filter(
                    Transfer.destination_location_id == location_id,
                    TransferLine.sku_id == sku_id,
                    Transfer.status.in_(["APPROVED", "DISPATCHED", "IN_TRANSIT"])
                )
            eligible_inbound = inbound_query.scalar() or 0
        else:
            # STRICT_ON_HAND_ONLY
            eligible_inbound = 0

        # 5. Core calculation
        # If policy specifically protects safety stock from commercial promises:
        atp_deduction = active_reservations + blocked + (safety_stock if protect_safety_stock_in_atp else 0)
        final_atp = max(0, on_hand - atp_deduction + eligible_inbound)

        reservable_stock = max(0, on_hand - blocked - active_reservations - safety_stock)

        # 6. Source movement references for auditability
        recent_movements = self.db.query(InventoryMovement.movement_id).filter(
            InventoryMovement.sku_id == sku_id,
            (InventoryMovement.destination_location_id == location_id) | (InventoryMovement.source_location_id == location_id)
        ).order_by(InventoryMovement.occurred_at.desc()).limit(5).all()
        source_refs = [m[0] for m in recent_movements]

        # 7. Explainable decision reason
        explanation_parts = [
            f"On-Hand: {on_hand}",
            f"Active Reservations: {active_reservations}",
            f"Blocked: {blocked}",
            f"Eligible Inbound ({inbound_policy}): {eligible_inbound}",
            f"Safety Stock ({safety_stock})" + (" [Protected in ATP]" if protect_safety_stock_in_atp else " [Protected in Reservable Stock]"),
            f"Computed ATP: {final_atp} units available to promise."
        ]
        decision_reason = " | ".join(explanation_parts)

        return ATPResponse(
            sku_id=sku_id,
            location_id=location_id,
            on_hand_stock=on_hand,
            reserved_stock=int(active_reservations),
            blocked_stock=blocked,
            safety_stock=safety_stock,
            eligible_inbound=int(eligible_inbound),
            final_atp=int(final_atp),
            reservable_stock=int(reservable_stock),
            calculation_timestamp=now,
            source_movement_references=source_refs,
            explanatory_decision_reason=decision_reason
        )
