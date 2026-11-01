from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app.models.entities import Product
from backend.app.schemas.schemas import ProductResponse, ProductCreate
import datetime

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("", response_model=List[ProductResponse])
def get_products(
    category: Optional[str] = None,
    brand: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    if brand:
        query = query.filter(Product.brand == brand)
    return query.offset(skip).limit(limit).all()

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.product_id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod

@router.post("", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    count = db.query(Product).count()
    prod_id = product.product_id or f"PRD-{count + 1:06d}"
    now = datetime.datetime.utcnow()
    new_prod = Product(
        product_id=prod_id,
        product_name=product.product_name,
        description=product.description,
        brand=product.brand,
        category=product.category,
        product_status=product.product_status,
        created_at=now,
        updated_at=now
    )
    db.add(new_prod)
    db.commit()
    db.refresh(new_prod)
    return new_prod
