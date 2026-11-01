from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from backend.app.database import get_db
from backend.app.models.entities import Order, OrderLine, Allocation
from backend.app.schemas.schemas import (
    OrderResponse,
    OrderCreate,
    AllocationDecisionResponse
)
from backend.app.services.order_engine import OrderEngine

router = APIRouter(prefix="/orders", tags=["Orders & Fulfillment"])

@router.get("", response_model=List[OrderResponse])
def get_orders(
    status: Optional[str] = None,
    channel: Optional[str] = None,
    customer_ref: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Order)
    if status:
        query = query.filter(Order.order_status == status)
    if channel:
        query = query.filter(Order.channel == channel)
    if customer_ref:
        query = query.filter(Order.customer_reference == customer_ref)
    return query.order_by(Order.order_date.desc()).offset(skip).limit(limit).all()

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, db: Session = Depends(get_db)):
    ord_obj = db.query(Order).filter(Order.order_id == order_id).first()
    if not ord_obj:
        raise HTTPException(status_code=404, detail="Order not found")
    return ord_obj

@router.post("", response_model=OrderResponse, status_code=201)
def create_order(
    order_in: OrderCreate,
    auto_allocate: bool = True,
    db: Session = Depends(get_db)
):
    engine = OrderEngine(db)
    lines_data = [l.model_dump() for l in order_in.lines]
    result = engine.create_order(
        customer_reference=order_in.customer_reference,
        lines=lines_data,
        channel=order_in.channel,
        requested_delivery_date=order_in.requested_delivery_date,
        auto_allocate=auto_allocate
    )
    return result["order"]

@router.post("/{order_id}/allocate")
def allocate_order(order_id: str, db: Session = Depends(get_db)):
    engine = OrderEngine(db)
    allocations = engine.allocate_order(order_id)
    if not allocations:
        raise HTTPException(status_code=400, detail="Could not allocate order lines or order not found")
    return {"order_id": order_id, "allocations": allocations}

@router.post("/{order_id}/fulfill")
def fulfill_order(
    order_id: str,
    carrier: str = "FedEx Express",
    tracking_reference: Optional[str] = None,
    db: Session = Depends(get_db)
):
    engine = OrderEngine(db)
    result = engine.fulfill_order(order_id, carrier=carrier, tracking_reference=tracking_reference)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@router.get("/{order_id}/allocations")
def get_order_allocations(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter_by(order_id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    line_ids = [l.order_line_id for l in order.order_lines]
    allocations = db.query(Allocation).filter(Allocation.order_line_id.in_(line_ids)).all()
    return allocations
