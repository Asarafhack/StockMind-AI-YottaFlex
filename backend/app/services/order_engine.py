import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.entities import (
    Order,
    OrderLine,
    Reservation,
    Allocation,
    Shipment,
    ShipmentLine,
    Location,
    SKU,
    InventoryBalance,
    AuditEvent
)
from backend.app.services.atp_engine import ATPEngine
from backend.app.services.reservation_engine import ReservationEngine
from backend.app.services.inventory_engine import InventoryEngine

class OrderEngine:
    def __init__(self, db: Session):
        self.db = db
        self.atp_engine = ATPEngine(db)
        self.reservation_engine = ReservationEngine(db)
        self.inventory_engine = InventoryEngine(db)

    def create_order(
        self,
        customer_reference: str,
        lines: List[Dict[str, Any]],
        channel: str = "ONLINE",
        requested_delivery_date: Optional[datetime.datetime] = None,
        auto_allocate: bool = True
    ) -> Dict[str, Any]:
        """
        Creates an order with order lines and optionally performs deterministic ATP allocation.
        """
        now = datetime.datetime.utcnow()
        count = self.db.query(func.count(Order.order_id)).scalar() or 0
        year = now.year
        order_id = f"ORD-{year}-{count + 1:06d}"

        total_amount = Decimal("0.0")
        order = Order(
            order_id=order_id,
            channel=channel,
            customer_reference=customer_reference,
            order_status="PENDING",
            order_date=now,
            requested_delivery_date=requested_delivery_date,
            total_amount=Decimal("0.0"),
            currency="USD"
        )
        self.db.add(order)
        self.db.flush()

        order_lines = []
        for idx, line in enumerate(lines, start=1):
            line_id = f"ORDL-{year}-{count + 1:06d}-{idx:02d}"
            sku_id = line["sku_id"]
            ordered_qty = line["ordered_quantity"]
            unit_price = Decimal(str(line.get("unit_price", 0.0)))
            total_amount += (unit_price * ordered_qty)

            order_line = OrderLine(
                order_line_id=line_id,
                order_id=order_id,
                sku_id=sku_id,
                ordered_quantity=ordered_qty,
                allocated_quantity=0,
                fulfilled_quantity=0,
                unit_price=unit_price,
                line_status="PENDING"
            )
            self.db.add(order_line)
            order_lines.append(order_line)

        order.total_amount = total_amount
        self.db.commit()

        allocation_results = []
        if auto_allocate:
            allocation_results = self.allocate_order(order_id)

        return {
            "order": order,
            "order_lines": order_lines,
            "allocations": allocation_results
        }

    def select_best_fulfillment_location(
        self,
        sku_id: str,
        required_quantity: int
    ) -> Optional[Dict[str, Any]]:
        """
        Deterministic location selection:
        Finds eligible active locations with sufficient reservable stock/ATP,
        prioritizing Warehouses/Distribution Centers first, then highest available stock.
        """
        balances = self.db.query(InventoryBalance, Location).join(
            Location, Location.location_id == InventoryBalance.location_id
        ).filter(
            InventoryBalance.sku_id == sku_id,
            Location.active_status == True
        ).all()

        candidate_evaluations = []
        for bal, loc in balances:
            atp_info = self.atp_engine.calculate_atp(sku_id, loc.location_id)
            if atp_info.reservable_stock > 0:
                # Priority score: Fulfillment Center/Warehouse higher priority than retail store
                type_priority = 3 if loc.location_type in ["Warehouse", "Distribution Center", "Fulfillment Center"] else 1
                candidate_evaluations.append({
                    "location_id": loc.location_id,
                    "location_name": loc.location_name,
                    "location_type": loc.location_type,
                    "reservable_stock": atp_info.reservable_stock,
                    "atp": atp_info.final_atp,
                    "priority_score": type_priority,
                    "explanation": atp_info.explanatory_decision_reason
                })

        if not candidate_evaluations:
            return None

        # Sort by: 1) ability to fulfill full order, 2) priority_score desc, 3) reservable_stock desc
        candidate_evaluations.sort(
            key=lambda x: (
                1 if x["reservable_stock"] >= required_quantity else 0,
                x["priority_score"],
                x["reservable_stock"]
            ),
            reverse=True
        )
        return candidate_evaluations[0]

    def allocate_order(self, order_id: str) -> List[Dict[str, Any]]:
        """
        Executes explainable allocation for each line in the order.
        """
        now = datetime.datetime.utcnow()
        order = self.db.query(Order).filter_by(order_id=order_id).first()
        if not order:
            return []

        allocations = []
        all_allocated = True
        any_allocated = False

        alc_count = self.db.query(func.count(Allocation.allocation_id)).scalar() or 0

        for line in order.order_lines:
            needed_qty = line.ordered_quantity - line.allocated_quantity
            if needed_qty <= 0:
                continue

            selection = self.select_best_fulfillment_location(line.sku_id, needed_qty)
            alc_count += 1
            allocation_id = f"ALC-{now.year}-{alc_count:06d}"

            if not selection:
                # Find candidate location evaluated for foreign key referential integrity
                fallback_loc = self.db.query(InventoryBalance.location_id).filter_by(sku_id=line.sku_id).first()
                eval_loc_id = fallback_loc[0] if fallback_loc else (self.db.query(Location.location_id).first()[0] if self.db.query(Location.location_id).first() else "LOC-000001")

                # REJECTED / BACKORDERED
                decision_reason = f"No eligible location has available reservable stock for SKU {line.sku_id}."
                alc = Allocation(
                    allocation_id=allocation_id,
                    order_line_id=line.order_line_id,
                    sku_id=line.sku_id,
                    location_id=eval_loc_id,
                    reservation_id=None,
                    allocated_quantity=0,
                    decision="REJECTED",
                    decision_reason=decision_reason,
                    allocated_at=now
                )
                self.db.add(alc)
                line.line_status = "BACKORDERED"
                all_allocated = False
                allocations.append({
                    "allocation_id": allocation_id,
                    "order_line_id": line.order_line_id,
                    "sku_id": line.sku_id,
                    "decision": "REJECTED",
                    "allocated_quantity": 0,
                    "reason": decision_reason
                })
                continue

            loc_id = selection["location_id"]
            avail = selection["reservable_stock"]
            qty_to_allocate = min(needed_qty, avail)

            # Create reservation
            res_result = self.reservation_engine.create_reservation(
                order_id=order.order_id,
                order_line_id=line.order_line_id,
                sku_id=line.sku_id,
                location_id=loc_id,
                quantity=qty_to_allocate
            )

            res_id = res_result["reservation"].reservation_id if res_result["success"] else None
            decision = "ACCEPTED" if qty_to_allocate == needed_qty else "PARTIAL"

            decision_reason = (
                f"Selected location {loc_id} ({selection['location_name']}) based on type {selection['location_type']} "
                f"and available stock {avail}. Allocated {qty_to_allocate}/{needed_qty} units. "
                f"Reservation {res_id} created."
            )

            alc = Allocation(
                allocation_id=allocation_id,
                order_line_id=line.order_line_id,
                sku_id=line.sku_id,
                location_id=loc_id,
                reservation_id=res_id,
                allocated_quantity=qty_to_allocate,
                decision=decision,
                decision_reason=decision_reason,
                allocated_at=now
            )
            self.db.add(alc)

            line.allocated_quantity += qty_to_allocate
            if line.allocated_quantity >= line.ordered_quantity:
                line.line_status = "ALLOCATED"
            else:
                line.line_status = "PARTIALLY_ALLOCATED"
                all_allocated = False

            any_allocated = True
            order.fulfillment_location_id = loc_id

            allocations.append({
                "allocation_id": allocation_id,
                "order_line_id": line.order_line_id,
                "sku_id": line.sku_id,
                "location_id": loc_id,
                "decision": decision,
                "allocated_quantity": qty_to_allocate,
                "reservation_id": res_id,
                "reason": decision_reason
            })

        if all_allocated and any_allocated:
            order.order_status = "ALLOCATED"
        elif any_allocated:
            order.order_status = "PARTIALLY_ALLOCATED"
        else:
            order.order_status = "BACKORDERED"

        self.db.commit()
        return allocations

    def fulfill_order(
        self,
        order_id: str,
        carrier: str = "FedEx Express",
        tracking_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fulfills allocated order:
        1. Consumes reservations.
        2. Records SALE movement in inventory ledger.
        3. Creates Shipment and ShipmentLines.
        4. Updates order and line statuses to SHIPPED.
        """
        now = datetime.datetime.utcnow()
        order = self.db.query(Order).filter_by(order_id=order_id).first()
        if not order:
            return {"success": False, "error": f"Order {order_id} not found"}

        if order.order_status not in ["ALLOCATED", "PARTIALLY_ALLOCATED"]:
            return {"success": False, "error": f"Order status is {order.order_status}, cannot fulfill without allocation."}

        origin_loc = order.fulfillment_location_id or "LOC-000001"
        shp_count = self.db.query(func.count(Shipment.shipment_id)).scalar() or 0
        year = now.year
        shipment_id = f"SHP-{year}-{shp_count + 1:06d}"
        if not tracking_reference:
            tracking_reference = f"TRK-{year}-{shp_count + 1:08d}"

        shipment = Shipment(
            shipment_id=shipment_id,
            order_id=order_id,
            origin_location_id=origin_loc,
            destination_location_id=None,
            shipment_status="SHIPPED",
            carrier=carrier,
            tracking_reference=tracking_reference,
            shipped_at=now
        )
        self.db.add(shipment)
        self.db.flush()

        fulfilled_lines = 0
        for line in order.order_lines:
            alloc_qty = line.allocated_quantity
            if alloc_qty <= 0:
                continue

            # 1. Consume reservation
            res = self.db.query(Reservation).filter_by(
                order_line_id=line.order_line_id,
                reservation_status="ACTIVE"
            ).first()
            if res:
                self.reservation_engine.consume_reservation_for_fulfillment(res.reservation_id)

            # 2. Record SALE movement (outbound)
            self.inventory_engine.record_movement(
                sku_id=line.sku_id,
                source_location_id=origin_loc,
                destination_location_id=None,
                movement_type="SALE",
                quantity=alloc_qty,
                reference_type="ORDER_FULFILLMENT",
                reference_id=order_id,
                reason_code="CUSTOMER_ORDER_FULFILLED",
                created_by="FULFILLMENT_ENGINE",
                metadata_json=f'{{"order_id": "{order_id}", "shipment_id": "{shipment_id}"}}',
                occurred_at=now
            )

            # 3. Add ShipmentLine
            shp_line_id = f"SHPL-{shipment_id}-{line.order_line_id.split('-')[-1]}"
            shp_line = ShipmentLine(
                shipment_line_id=shp_line_id,
                shipment_id=shipment_id,
                order_line_id=line.order_line_id,
                sku_id=line.sku_id,
                quantity=alloc_qty
            )
            self.db.add(shp_line)

            line.fulfilled_quantity += alloc_qty
            line.line_status = "FULFILLED"
            fulfilled_lines += 1

        order.order_status = "SHIPPED"
        self.db.commit()

        return {
            "success": True,
            "order_id": order_id,
            "shipment_id": shipment_id,
            "tracking_reference": tracking_reference,
            "fulfilled_lines": fulfilled_lines
        }
