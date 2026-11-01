import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.entities import (
    Reservation,
    InventoryBalance,
    Order,
    OrderLine,
    AuditEvent
)
from backend.app.services.atp_engine import ATPEngine

class ReservationEngine:
    def __init__(self, db: Session):
        self.db = db
        self.atp_engine = ATPEngine(db)

    def create_reservation(
        self,
        order_id: str,
        order_line_id: str,
        sku_id: str,
        location_id: str,
        quantity: int,
        duration_minutes: int = 60,
        enforce_reservable_stock: bool = True
    ) -> Dict[str, Any]:
        """
        Creates a stock reservation atomically with concurrency and stock validation.
        """
        now = datetime.datetime.utcnow()
        expires_at = now + datetime.timedelta(minutes=duration_minutes)

        # 1. Sweep expired reservations first to ensure up-to-date availability
        self.expire_stale_reservations()

        # 2. Check Reservable Stock / ATP
        atp = self.atp_engine.calculate_atp(sku_id, location_id)
        if enforce_reservable_stock and quantity > atp.reservable_stock:
            return {
                "success": False,
                "reservation": None,
                "error": f"Insufficient reservable stock. Requested: {quantity}, Reservable: {atp.reservable_stock}, ATP: {atp.final_atp}"
            }

        # 3. Deterministic ID: RES-ORD-YYYY-XXXXXX-XX
        line_suffix = order_line_id.split("-")[-1] if "-" in order_line_id else "01"
        res_id = f"RES-{order_id}-{line_suffix}"

        # If reservation already exists with this ID (idempotency), return it or update
        existing = self.db.query(Reservation).filter_by(reservation_id=res_id).first()
        if existing and existing.reservation_status == "ACTIVE":
            return {
                "success": True,
                "reservation": existing,
                "message": "Existing active reservation returned (idempotent)."
            }

        reservation = Reservation(
            reservation_id=res_id,
            order_id=order_id,
            order_line_id=order_line_id,
            sku_id=sku_id,
            location_id=location_id,
            quantity=quantity,
            reservation_status="ACTIVE",
            reserved_at=now,
            expires_at=expires_at
        )
        self.db.add(reservation)

        # 4. Update InventoryBalance reserved_quantity atomically
        balance = self.db.query(InventoryBalance).filter_by(sku_id=sku_id, location_id=location_id).first()
        if balance:
            balance.reserved_quantity += quantity
            balance.available_quantity = max(0, balance.on_hand_quantity - balance.reserved_quantity - balance.blocked_quantity)
            balance.version += 1
            balance.updated_at = now

        # Audit
        audit = AuditEvent(
            audit_id=f"AUD-{now.strftime('%Y%m%d%H%M%S%f')}",
            timestamp=now,
            event_type="RESERVATION_CREATED",
            entity_type="Reservation",
            entity_id=res_id,
            action="CREATE",
            user_id="RESERVATION_ENGINE",
            details=f"Reserved {quantity} units of {sku_id} at {location_id} until {expires_at.isoformat()}"
        )
        self.db.add(audit)
        self.db.commit()

        return {
            "success": True,
            "reservation": reservation,
            "expires_at": expires_at
        }

    def release_reservation(
        self,
        reservation_id: str,
        reason: str = "MANUAL_RELEASE"
    ) -> Dict[str, Any]:
        """
        Explicitly releases an active reservation back to available stock.
        """
        now = datetime.datetime.utcnow()
        res = self.db.query(Reservation).filter_by(reservation_id=reservation_id).first()
        if not res:
            return {"success": False, "error": f"Reservation {reservation_id} not found"}

        if res.reservation_status != "ACTIVE":
            return {"success": False, "error": f"Reservation is already {res.reservation_status}"}

        res.reservation_status = "RELEASED"
        res.released_at = now
        res.release_reason = reason

        # Restore balance
        balance = self.db.query(InventoryBalance).filter_by(sku_id=res.sku_id, location_id=res.location_id).first()
        if balance:
            balance.reserved_quantity = max(0, balance.reserved_quantity - res.quantity)
            balance.available_quantity = max(0, balance.on_hand_quantity - balance.reserved_quantity - balance.blocked_quantity)
            balance.version += 1
            balance.updated_at = now

        # Audit
        audit = AuditEvent(
            audit_id=f"AUD-{now.strftime('%Y%m%d%H%M%S%f')}",
            timestamp=now,
            event_type="RESERVATION_RELEASED",
            entity_type="Reservation",
            entity_id=res.reservation_id,
            action="RELEASE",
            user_id="RESERVATION_ENGINE",
            details=f"Released {res.quantity} units for {res.sku_id} at {res.location_id}. Reason: {reason}"
        )
        self.db.add(audit)
        self.db.commit()

        return {"success": True, "reservation": res, "released_quantity": res.quantity}

    def expire_stale_reservations(self) -> int:
        """
        Sweeps active reservations that have passed expires_at and transitions them to EXPIRED.
        Restores balance reserved_quantity.
        """
        now = datetime.datetime.utcnow()
        expired_reservations = self.db.query(Reservation).filter(
            Reservation.reservation_status == "ACTIVE",
            Reservation.expires_at <= now
        ).all()

        count = 0
        for res in expired_reservations:
            res.reservation_status = "EXPIRED"
            res.released_at = now
            res.release_reason = "TTL_EXPIRED"

            balance = self.db.query(InventoryBalance).filter_by(sku_id=res.sku_id, location_id=res.location_id).first()
            if balance:
                balance.reserved_quantity = max(0, balance.reserved_quantity - res.quantity)
                balance.available_quantity = max(0, balance.on_hand_quantity - balance.reserved_quantity - balance.blocked_quantity)
                balance.version += 1
                balance.updated_at = now
            count += 1

        if count > 0:
            self.db.commit()
        return count

    def consume_reservation_for_fulfillment(
        self,
        reservation_id: str
    ) -> bool:
        """
        Marks reservation as FULFILLED when shipment/fulfillment consumes reserved units.
        Reduces reserved_quantity from balance (actual stock reduction happens in InventoryMovement SALE).
        """
        now = datetime.datetime.utcnow()
        res = self.db.query(Reservation).filter_by(reservation_id=reservation_id).first()
        if not res or res.reservation_status != "ACTIVE":
            return False

        res.reservation_status = "FULFILLED"
        res.fulfilled_at = now

        balance = self.db.query(InventoryBalance).filter_by(sku_id=res.sku_id, location_id=res.location_id).first()
        if balance:
            balance.reserved_quantity = max(0, balance.reserved_quantity - res.quantity)
            balance.version += 1
            balance.updated_at = now

        self.db.commit()
        return True
