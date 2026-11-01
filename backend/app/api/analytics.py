from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import Dict, Any, List
from backend.app.database import get_db
from backend.app.models.entities import (
    SKU, Location, Product, InventoryBalance, InventoryMovement,
    Order, OrderLine, Reservation, AnomalyRecord
)
from backend.app.schemas.schemas import KPIOverview

router = APIRouter(prefix="/analytics", tags=["Analytics & BI"])

@router.get("/overview", response_model=KPIOverview)
def get_analytics_overview(db: Session = Depends(get_db)):
    total_skus = db.query(func.count(SKU.sku_id)).scalar() or 0
    total_locations = db.query(func.count(Location.location_id)).scalar() or 0

    balance_aggregates = db.query(
        func.coalesce(func.sum(InventoryBalance.on_hand_quantity), 0),
        func.coalesce(func.sum(InventoryBalance.available_quantity), 0),
        func.coalesce(func.sum(InventoryBalance.reserved_quantity), 0),
        func.coalesce(func.sum(InventoryBalance.in_transit_quantity), 0),
        func.coalesce(func.sum(InventoryBalance.blocked_quantity), 0)
    ).first()

    on_hand = balance_aggregates[0]
    avail_atp = balance_aggregates[1]
    reserved = balance_aggregates[2]
    in_transit = balance_aggregates[3]

    open_orders = db.query(func.count(Order.order_id)).filter(
        Order.order_status.in_(["PENDING", "ALLOCATED", "PARTIALLY_ALLOCATED", "BACKORDERED"])
    ).scalar() or 0

    total_order_lines = db.query(func.count(OrderLine.order_line_id)).scalar() or 0
    fulfilled_order_lines = db.query(func.count(OrderLine.order_line_id)).filter(
        OrderLine.line_status == "FULFILLED"
    ).scalar() or 0
    fulfillment_rate = (fulfilled_order_lines / total_order_lines * 100) if total_order_lines > 0 else 100.0

    total_balances = db.query(func.count(InventoryBalance.balance_id)).scalar() or 0
    stockout_balances = db.query(func.count(InventoryBalance.balance_id)).filter(
        InventoryBalance.available_quantity == 0
    ).scalar() or 0
    stockout_rate = (stockout_balances / total_balances * 100) if total_balances > 0 else 0.0

    total_reservations = db.query(func.count(Reservation.reservation_id)).scalar() or 0
    expired_reservations = db.query(func.count(Reservation.reservation_id)).filter(
        Reservation.reservation_status == "EXPIRED"
    ).scalar() or 0
    expiry_rate = (expired_reservations / total_reservations * 100) if total_reservations > 0 else 0.0

    total_anomalies = db.query(func.count(AnomalyRecord.anomaly_id)).scalar() or 0
    critical_anomalies = db.query(func.count(AnomalyRecord.anomaly_id)).filter(
        AnomalyRecord.severity == "CRITICAL"
    ).scalar() or 0
    open_anomalies = db.query(func.count(AnomalyRecord.anomaly_id)).filter(
        AnomalyRecord.status == "OPEN"
    ).scalar() or 0

    # Accuracy: percentage of balances without anomaly
    balance_anomalies = db.query(func.count(distinct(AnomalyRecord.affected_sku))).filter(
        AnomalyRecord.issue_type == "BALANCE_MISMATCH"
    ).scalar() or 0
    accuracy = max(0.0, min(100.0, (1.0 - (balance_anomalies / max(1, total_skus))) * 100.0))

    return KPIOverview(
        total_skus=total_skus,
        total_locations=total_locations,
        total_on_hand_inventory=on_hand,
        available_to_promise_quantity=avail_atp,
        active_reservations=reserved,
        in_transit_inventory=in_transit,
        open_orders=open_orders,
        fulfillment_rate_pct=round(fulfillment_rate, 2),
        inventory_accuracy_pct=round(accuracy, 2),
        total_anomalies=total_anomalies,
        critical_anomalies=critical_anomalies,
        open_anomalies=open_anomalies,
        stockout_rate_pct=round(stockout_rate, 2),
        reservation_expiry_rate_pct=round(expiry_rate, 2)
    )

@router.get("/charts/location-distribution")
def get_location_inventory_distribution(db: Session = Depends(get_db)):
    results = db.query(
        Location.location_name,
        Location.location_type,
        func.coalesce(func.sum(InventoryBalance.on_hand_quantity), 0).label("on_hand"),
        func.coalesce(func.sum(InventoryBalance.available_quantity), 0).label("available"),
        func.coalesce(func.sum(InventoryBalance.reserved_quantity), 0).label("reserved")
    ).join(
        InventoryBalance, InventoryBalance.location_id == Location.location_id
    ).group_by(Location.location_id).limit(15).all()

    return [
        {
            "location_name": r[0],
            "location_type": r[1],
            "on_hand": r[2],
            "available": r[3],
            "reserved": r[4]
        } for r in results
    ]

@router.get("/charts/category-distribution")
def get_category_distribution(db: Session = Depends(get_db)):
    results = db.query(
        Product.category,
        func.coalesce(func.sum(InventoryBalance.on_hand_quantity), 0).label("total_units"),
        func.coalesce(func.sum(InventoryBalance.on_hand_quantity * SKU.selling_price), 0).label("total_value")
    ).join(
        SKU, SKU.product_id == Product.product_id
    ).join(
        InventoryBalance, InventoryBalance.sku_id == SKU.sku_id
    ).group_by(Product.category).all()

    return [
        {
            "category": r[0],
            "total_units": r[1],
            "total_value": float(round(r[2], 2))
        } for r in results
    ]

@router.get("/charts/movement-breakdown")
def get_movement_breakdown(db: Session = Depends(get_db)):
    results = db.query(
        InventoryMovement.movement_type,
        func.count(InventoryMovement.movement_id).label("count"),
        func.coalesce(func.sum(InventoryMovement.quantity), 0).label("total_quantity")
    ).group_by(InventoryMovement.movement_type).all()

    return [
        {
            "movement_type": r[0],
            "count": r[1],
            "total_quantity": r[2]
        } for r in results
    ]

@router.get("/what-if/simulate")
def simulate_what_if_scenario(
    demand_surge_pct: float = Query(25.0, description="Projected demand increase %"),
    lead_time_delay_days: int = Query(5, description="Supplier transit delay in days"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Non-destructive digital twin what-if simulation:
    Simulates demand surges and supply delays on current ATP and stockout exposure.
    """
    total_balances = db.query(InventoryBalance).count()
    current_atp_sum = db.query(func.coalesce(func.sum(InventoryBalance.available_quantity), 0)).scalar() or 0
    current_stockouts = db.query(func.count(InventoryBalance.balance_id)).filter(
        InventoryBalance.available_quantity == 0
    ).scalar() or 0

    # Under demand surge: additional reservations consume available stock
    surge_multiplier = (1.0 + (demand_surge_pct / 100.0))
    simulated_atp = max(0, int(current_atp_sum / surge_multiplier))

    # Balances at risk (where available stock <= current safety stock)
    at_risk_count = db.query(func.count(InventoryBalance.balance_id)).filter(
        InventoryBalance.available_quantity <= InventoryBalance.safety_stock_quantity
    ).scalar() or 0

    simulated_stockouts = current_stockouts + int(at_risk_count * (demand_surge_pct / 100.0) * (lead_time_delay_days / 5.0))
    simulated_stockouts = min(total_balances, simulated_stockouts)

    return {
        "scenario_parameters": {
            "demand_surge_pct": demand_surge_pct,
            "lead_time_delay_days": lead_time_delay_days
        },
        "baseline": {
            "available_to_promise": current_atp_sum,
            "stockout_locations_count": current_stockouts,
            "stockout_rate_pct": round((current_stockouts / max(1, total_balances)) * 100.0, 2)
        },
        "projected_simulation": {
            "projected_available_to_promise": simulated_atp,
            "projected_stockout_locations": simulated_stockouts,
            "projected_stockout_rate_pct": round((simulated_stockouts / max(1, total_balances)) * 100.0, 2),
            "atp_reduction_pct": round(((current_atp_sum - simulated_atp) / max(1, current_atp_sum)) * 100.0, 2),
            "recommendation": (
                f"Under a {demand_surge_pct}% demand surge combined with {lead_time_delay_days} days supplier delay, "
                f"stockouts increase by {simulated_stockouts - current_stockouts} SKU-location units. "
                f"Proactively increase safety stock buffers on high-velocity items."
            )
        }
    }
