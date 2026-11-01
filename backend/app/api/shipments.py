from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app.models.entities import Shipment
from backend.app.schemas.schemas import ShipmentResponse

router = APIRouter(prefix="/shipments", tags=["Shipments"])

@router.get("", response_model=List[ShipmentResponse])
def get_shipments(
    status: Optional[str] = None,
    order_id: Optional[str] = None,
    carrier: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Shipment)
    if status:
        query = query.filter(Shipment.shipment_status == status)
    if order_id:
        query = query.filter(Shipment.order_id == order_id)
    if carrier:
        query = query.filter(Shipment.carrier == carrier)
    return query.order_by(Shipment.shipped_at.desc()).offset(skip).limit(limit).all()

@router.get("/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(shipment_id: str, db: Session = Depends(get_db)):
    shp = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
    if not shp:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shp
