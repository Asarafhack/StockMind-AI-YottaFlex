from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app.models.entities import SKU, Product
from backend.app.schemas.schemas import SKUResponse, SKUCreate
import datetime

router = APIRouter(prefix="/skus", tags=["SKUs"])

@router.get("", response_model=List[SKUResponse])
def get_skus(
    product_id: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(SKU)
    if product_id:
        query = query.filter(SKU.product_id == product_id)
    if status:
        query = query.filter(SKU.status == status)
    if search:
        query = query.filter(SKU.sku_code.ilike(f"%{search}%") | SKU.variant.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()

@router.get("/{sku_id}", response_model=SKUResponse)
def get_sku(sku_id: str, db: Session = Depends(get_db)):
    sku = db.query(SKU).filter(SKU.sku_id == sku_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    return sku

@router.post("", response_model=SKUResponse, status_code=201)
def create_sku(sku_in: SKUCreate, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.product_id == sku_in.product_id).first()
    if not prod:
        raise HTTPException(status_code=400, detail="Referenced product_id does not exist")

    count = db.query(SKU).count()
    sku_id = sku_in.sku_id or f"SKU-{count + 1:06d}"
    now = datetime.datetime.utcnow()
    new_sku = SKU(
        sku_id=sku_id,
        product_id=sku_in.product_id,
        sku_code=sku_in.sku_code,
        barcode=sku_in.barcode,
        variant=sku_in.variant,
        unit_of_measure=sku_in.unit_of_measure,
        unit_cost=sku_in.unit_cost,
        selling_price=sku_in.selling_price,
        weight=sku_in.weight,
        status=sku_in.status,
        created_at=now
    )
    db.add(new_sku)
    db.commit()
    db.refresh(new_sku)
    return new_sku
