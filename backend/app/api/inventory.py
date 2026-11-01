from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from backend.app.database import get_db
from backend.app.models.entities import InventoryBalance, InventoryMovement, SKU, Location
from backend.app.schemas.schemas import (
    InventoryBalanceResponse,
    InventoryMovementCreate,
    InventoryMovementResponse,
    ATPResponse
)
from backend.app.services.inventory_engine import InventoryEngine
from backend.app.services.atp_engine import ATPEngine

router = APIRouter(prefix="/inventory", tags=["Inventory & Ledger"])

@router.get("", response_model=List[InventoryBalanceResponse])
def get_inventory_balances(
    sku_id: Optional[str] = None,
    location_id: Optional[str] = None,
    status: Optional[str] = None,  # HEALTHY, LOW_STOCK, STOCKOUT, OVERSTOCK, BLOCKED, RECONCILIATION_REQUIRED
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(InventoryBalance)
    if sku_id:
        query = query.filter(InventoryBalance.sku_id == sku_id)
    if location_id:
        query = query.filter(InventoryBalance.location_id == location_id)

    if status == "STOCKOUT":
        query = query.filter(InventoryBalance.available_quantity == 0)
    elif status == "LOW_STOCK":
        query = query.filter(InventoryBalance.available_quantity > 0, InventoryBalance.available_quantity <= InventoryBalance.safety_stock_quantity)
    elif status == "BLOCKED":
        query = query.filter(InventoryBalance.blocked_quantity > 0)
    elif status == "HEALTHY":
        query = query.filter(InventoryBalance.available_quantity > InventoryBalance.safety_stock_quantity)

    return query.offset(skip).limit(limit).all()

@router.get("/{sku_id}/{location_id}", response_model=InventoryBalanceResponse)
def get_inventory_balance_item(sku_id: str, location_id: str, db: Session = Depends(get_db)):
    bal = db.query(InventoryBalance).filter_by(sku_id=sku_id, location_id=location_id).first()
    if not bal:
        raise HTTPException(status_code=404, detail="Inventory balance record not found")
    return bal

@router.get("/{sku_id}/{location_id}/atp", response_model=ATPResponse)
def get_sku_location_atp(
    sku_id: str,
    location_id: str,
    protect_safety_stock: bool = False,
    db: Session = Depends(get_db)
):
    atp_engine = ATPEngine(db)
    return atp_engine.calculate_atp(sku_id, location_id, protect_safety_stock_in_atp=protect_safety_stock)

@router.post("/{sku_id}/{location_id}/reconcile")
def reconcile_inventory(sku_id: str, location_id: str, db: Session = Depends(get_db)):
    inv_engine = InventoryEngine(db)
    return inv_engine.reconcile_balance(sku_id, location_id)

@router.post("/{sku_id}/{location_id}/compensate")
def compensate_inventory(
    sku_id: str,
    location_id: str,
    reason: str = "MANUAL_RECONCILIATION",
    db: Session = Depends(get_db)
):
    inv_engine = InventoryEngine(db)
    mov = inv_engine.record_compensating_adjustment(sku_id, location_id, reason=reason)
    if not mov:
        return {"status": "NO_ACTION_REQUIRED", "message": "Balances are already reconciled"}
    return {
        "status": "COMPENSATED",
        "movement_id": mov.movement_id,
        "movement_type": mov.movement_type,
        "quantity": mov.quantity
    }

# Movements
@router.get("/movements/all", response_model=List[InventoryMovementResponse])
def get_movements(
    sku_id: Optional[str] = None,
    location_id: Optional[str] = None,
    movement_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(InventoryMovement)
    if sku_id:
        query = query.filter(InventoryMovement.sku_id == sku_id)
    if location_id:
        query = query.filter(
            (InventoryMovement.destination_location_id == location_id) |
            (InventoryMovement.source_location_id == location_id)
        )
    if movement_type:
        query = query.filter(InventoryMovement.movement_type == movement_type)

    return query.order_by(InventoryMovement.occurred_at.desc()).offset(skip).limit(limit).all()

@router.post("/movements/record", response_model=InventoryMovementResponse, status_code=201)
def record_inventory_movement(
    mov_in: InventoryMovementCreate,
    db: Session = Depends(get_db)
):
    inv_engine = InventoryEngine(db)
    movement = inv_engine.record_movement(
        sku_id=mov_in.sku_id,
        source_location_id=mov_in.source_location_id,
        destination_location_id=mov_in.destination_location_id,
        movement_type=mov_in.movement_type,
        quantity=mov_in.quantity,
        reference_type=mov_in.reference_type,
        reference_id=mov_in.reference_id,
        transfer_id=mov_in.transfer_id,
        reason_code=mov_in.reason_code,
        created_by=mov_in.created_by,
        metadata_json=mov_in.metadata_json
    )
    return movement
