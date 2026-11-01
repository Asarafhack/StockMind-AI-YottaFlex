from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from backend.app.database import get_db
from backend.app.models.entities import ReplenishmentRule, InventoryBalance, SKU, Location
from backend.app.schemas.schemas import ReplenishmentRuleResponse
from backend.app.services.atp_engine import ATPEngine

router = APIRouter(prefix="/replenishment", tags=["Replenishment"])

@router.get("/rules", response_model=List[ReplenishmentRuleResponse])
def get_replenishment_rules(
    sku_id: Optional[str] = None,
    location_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(ReplenishmentRule).filter(ReplenishmentRule.is_active == True)
    if sku_id:
        query = query.filter(ReplenishmentRule.sku_id == sku_id)
    if location_id:
        query = query.filter(ReplenishmentRule.location_id == location_id)
    return query.offset(skip).limit(limit).all()

@router.get("/recommendations")
def get_replenishment_recommendations(
    location_id: Optional[str] = None,
    urgency_only: bool = False,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Evaluates current inventory levels against replenishment policies.
    Flags items where Available + Eligible Inbound <= Reorder Point.
    """
    query = db.query(ReplenishmentRule, InventoryBalance, SKU, Location).join(
        InventoryBalance,
        (InventoryBalance.sku_id == ReplenishmentRule.sku_id) &
        (InventoryBalance.location_id == ReplenishmentRule.location_id)
    ).join(
        SKU, SKU.sku_id == ReplenishmentRule.sku_id
    ).join(
        Location, Location.location_id == ReplenishmentRule.location_id
    ).filter(ReplenishmentRule.is_active == True)

    if location_id:
        query = query.filter(ReplenishmentRule.location_id == location_id)

    records = query.all()
    recommendations = []
    atp_engine = ATPEngine(db)

    for rule, bal, sku, loc in records:
        effective_stock = bal.available_quantity + bal.in_transit_quantity
        needs_reorder = effective_stock <= rule.reorder_point
        is_critical = bal.available_quantity <= rule.safety_stock

        if urgency_only and not is_critical:
            continue

        if needs_reorder:
            urgency = "CRITICAL" if bal.available_quantity == 0 else ("HIGH" if is_critical else "MEDIUM")
            deficit = max(0, rule.maximum_stock - effective_stock)
            rec_qty = max(rule.reorder_quantity, deficit)

            recommendations.append({
                "rule_id": rule.rule_id,
                "sku_id": sku.sku_id,
                "sku_code": sku.sku_code,
                "variant": sku.variant,
                "location_id": loc.location_id,
                "location_name": loc.location_name,
                "location_type": loc.location_type,
                "current_on_hand": bal.on_hand_quantity,
                "available_stock": bal.available_quantity,
                "in_transit": bal.in_transit_quantity,
                "effective_stock": effective_stock,
                "reorder_point": rule.reorder_point,
                "safety_stock": rule.safety_stock,
                "recommended_order_quantity": rec_qty,
                "lead_time_days": rule.lead_time_days,
                "urgency": urgency,
                "estimated_cost": float(sku.unit_cost * rec_qty),
                "reason": (
                    f"Effective stock ({effective_stock}) is below reorder point ({rule.reorder_point}). "
                    f"Safety stock buffer is {rule.safety_stock} units."
                )
            })

    # Sort by urgency
    urgency_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
    recommendations.sort(key=lambda x: urgency_order.get(x["urgency"], 3))
    return recommendations
