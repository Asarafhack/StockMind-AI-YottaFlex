from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app.models.entities import Reservation
from backend.app.schemas.schemas import ReservationResponse, ReservationCreate
from backend.app.services.reservation_engine import ReservationEngine

router = APIRouter(prefix="/reservations", tags=["Reservations"])

@router.get("", response_model=List[ReservationResponse])
def get_reservations(
    status: Optional[str] = None,
    order_id: Optional[str] = None,
    sku_id: Optional[str] = None,
    location_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Reservation)
    if status:
        query = query.filter(Reservation.reservation_status == status)
    if order_id:
        query = query.filter(Reservation.order_id == order_id)
    if sku_id:
        query = query.filter(Reservation.sku_id == sku_id)
    if location_id:
        query = query.filter(Reservation.location_id == location_id)
    return query.order_by(Reservation.reserved_at.desc()).offset(skip).limit(limit).all()

@router.post("", response_model=ReservationResponse, status_code=201)
def create_reservation(
    res_in: ReservationCreate,
    db: Session = Depends(get_db)
):
    res_engine = ReservationEngine(db)
    result = res_engine.create_reservation(
        order_id=res_in.order_id,
        order_line_id=res_in.order_line_id,
        sku_id=res_in.sku_id,
        location_id=res_in.location_id,
        quantity=res_in.quantity,
        duration_minutes=res_in.duration_minutes
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Reservation failed"))
    return result["reservation"]

@router.post("/{reservation_id}/release")
def release_reservation(
    reservation_id: str,
    reason: str = "MANUAL_OPERATOR_RELEASE",
    db: Session = Depends(get_db)
):
    res_engine = ReservationEngine(db)
    result = res_engine.release_reservation(reservation_id, reason=reason)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@router.post("/sweep-expired")
def sweep_expired_reservations(db: Session = Depends(get_db)):
    res_engine = ReservationEngine(db)
    count = res_engine.expire_stale_reservations()
    return {"status": "SUCCESS", "expired_reservations_count": count}
