from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app.models.entities import Transfer
from backend.app.schemas.schemas import TransferResponse, TransferCreate
from backend.app.services.transfer_engine import TransferEngine

router = APIRouter(prefix="/transfers", tags=["Transfers"])

@router.get("", response_model=List[TransferResponse])
def get_transfers(
    status: Optional[str] = None,
    source_location_id: Optional[str] = None,
    destination_location_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Transfer)
    if status:
        query = query.filter(Transfer.status == status)
    if source_location_id:
        query = query.filter(Transfer.source_location_id == source_location_id)
    if destination_location_id:
        query = query.filter(Transfer.destination_location_id == destination_location_id)
    return query.order_by(Transfer.requested_at.desc()).offset(skip).limit(limit).all()

@router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer(transfer_id: str, db: Session = Depends(get_db)):
    trn = db.query(Transfer).filter(Transfer.transfer_id == transfer_id).first()
    if not trn:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return trn

@router.post("", response_model=TransferResponse, status_code=201)
def create_transfer(
    trn_in: TransferCreate,
    db: Session = Depends(get_db)
):
    engine = TransferEngine(db)
    lines_data = [l.model_dump() for l in trn_in.lines]
    trn = engine.create_transfer(
        source_location_id=trn_in.source_location_id,
        destination_location_id=trn_in.destination_location_id,
        lines=lines_data,
        carrier=trn_in.carrier,
        tracking_reference=trn_in.tracking_reference,
        notes=trn_in.notes
    )
    return trn

@router.post("/{transfer_id}/approve")
def approve_transfer(transfer_id: str, db: Session = Depends(get_db)):
    engine = TransferEngine(db)
    result = engine.approve_transfer(transfer_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@router.post("/{transfer_id}/dispatch")
def dispatch_transfer(
    transfer_id: str,
    carrier: Optional[str] = None,
    tracking_reference: Optional[str] = None,
    db: Session = Depends(get_db)
):
    engine = TransferEngine(db)
    result = engine.dispatch_transfer(transfer_id, carrier=carrier, tracking_reference=tracking_reference)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@router.post("/{transfer_id}/receive")
def receive_transfer(transfer_id: str, db: Session = Depends(get_db)):
    engine = TransferEngine(db)
    result = engine.receive_transfer(transfer_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@router.post("/{transfer_id}/cancel")
def cancel_transfer(transfer_id: str, reason: str = "CANCELLED_BY_OPERATOR", db: Session = Depends(get_db)):
    engine = TransferEngine(db)
    result = engine.cancel_transfer(transfer_id, reason=reason)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
