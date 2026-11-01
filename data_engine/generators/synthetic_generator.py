import datetime
import hashlib
import json
import os
import random
from decimal import Decimal
from typing import Dict, Any, List, Tuple, Generator
import numpy as np
from faker import Faker

# Deterministic prefixes
PROD_PREFIX = "PRD"
SKU_PREFIX = "SKU"
LOC_PREFIX = "LOC"
ORD_PREFIX = "ORD"
RES_PREFIX = "RES"
MOV_PREFIX = "MOV"
SHP_PREFIX = "SHP"
TRN_PREFIX = "TRN"
RPL_PREFIX = "RPL"
ANOM_PREFIX = "ANOM"

CATEGORIES = [
    "Electronics", "Apparel", "Home & Garden", "Health & Beauty",
    "Sports & Outdoors", "Automotive", "Toys & Games", "Office Supplies"
]

BRANDS = [
    "ApexDynamics", "NordicEdge", "TerraForm", "QuantumCore",
    "AeroTech", "LuminaStyle", "EchoWave", "VanguardPrime"
]

LOCATION_TYPES = [
    ("Warehouse", 0.25),
    ("Distribution Center", 0.20),
    ("Fulfillment Center", 0.25),
    ("Retail Store", 0.20),
    ("Online Channel", 0.10)
]

MOVEMENT_TYPES = [
    ("RECEIPT", 0.28),
    ("SALE", 0.38),
    ("TRANSFER_DISPATCH", 0.12),
    ("TRANSFER_RECEIPT", 0.12),
    ("ADJUSTMENT_IN", 0.03),
    ("ADJUSTMENT_OUT", 0.03),
    ("CUSTOMER_RETURN", 0.02),
    ("DAMAGE", 0.01),
    ("BLOCK", 0.005),
    ("UNBLOCK", 0.005)
]

class SyntheticDataGenerator:
    def __init__(self, seed: int = 20261022):
        self.seed = seed
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)
        self.faker = Faker()
        self.faker.seed_instance(seed)
        self.base_date = datetime.datetime(2026, 1, 1, 0, 0, 0)

    # 1. Products Generator
    def generate_products(self, count: int) -> List[Dict[str, Any]]:
        products = []
        for i in range(1, count + 1):
            category = self.rng.choice(CATEGORIES)
            brand = self.rng.choice(BRANDS)
            name = f"{brand} {category} Pro Model {i}"
            products.append({
                "product_id": f"{PROD_PREFIX}-{i:06d}",
                "product_name": name,
                "description": f"High performance {category.lower()} unit manufactured by {brand}.",
                "brand": brand,
                "category": category,
                "product_status": "ACTIVE",
                "created_at": self.base_date,
                "updated_at": self.base_date
            })
        return products

    # 2. Locations Generator
    def generate_locations(self, count: int) -> List[Dict[str, Any]]:
        locations = []
        types, weights = zip(*LOCATION_TYPES)
        # Choose types deterministically
        loc_types = self.rng.choices(types, weights=weights, k=count)
        # Ensure at least 1 warehouse and 1 distribution center
        if count >= 2:
            loc_types[0] = "Warehouse"
            loc_types[1] = "Distribution Center"

        for i in range(1, count + 1):
            loc_id = f"{LOC_PREFIX}-{i:06d}"
            loc_type = loc_types[i - 1]
            city = self.faker.city()
            state = self.faker.state_abbr()
            name = f"{city} {loc_type} #{i}"
            parent_id = f"{LOC_PREFIX}-000001" if (loc_type in ["Retail Store", "Fulfillment Center"] and i > 1) else None

            locations.append({
                "location_id": loc_id,
                "location_code": f"LC-{i:04d}",
                "location_name": name,
                "location_type": loc_type,
                "parent_location_id": parent_id,
                "address": f"{100 + i} Industrial Blvd",
                "city": city,
                "region": state,
                "country": "USA",
                "timezone": "America/New_York",
                "active_status": True,
                "created_at": self.base_date
            })
        return locations

    # 3. SKUs Generator
    def generate_skus(self, count: int, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        skus = []
        num_products = len(products)
        variants = ["Standard", "Large", "Small", "Deluxe", "Eco", "Pro", "Midnight Navy", "Matte Black"]

        for i in range(1, count + 1):
            prod = products[(i - 1) % num_products]
            variant = self.rng.choice(variants)
            cost = round(self.rng.uniform(10.0, 350.0), 2)
            margin = self.rng.uniform(1.25, 2.2)
            selling_price = round(cost * margin, 2)
            weight = round(self.rng.uniform(0.5, 25.0), 2)

            skus.append({
                "sku_id": f"{SKU_PREFIX}-{i:06d}",
                "product_id": prod["product_id"],
                "sku_code": f"SKU-{prod['brand'][:3].upper()}-{i:06d}",
                "barcode": f"0123456{i:06d}",
                "variant": variant,
                "unit_of_measure": "EACH",
                "unit_cost": cost,
                "selling_price": selling_price,
                "weight": weight,
                "status": "ACTIVE",
                "created_at": self.base_date
            })
        return skus

    # 4. Replenishment Rules Generator
    def generate_replenishment_rules(
        self,
        skus: List[Dict[str, Any]],
        locations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        rules = []
        rule_idx = 1
        policies = ["ALLOW_CONFIRMED_IN_TRANSIT", "ALLOW_ALL_IN_TRANSIT", "STRICT_ON_HAND_ONLY"]

        for loc in locations:
            for sku in skus:
                safety = self.rng.randint(15, 60)
                reorder_pt = safety + self.rng.randint(20, 80)
                reorder_qty = self.rng.randint(50, 200)
                max_stock = reorder_pt + reorder_qty + 50
                lead_time = self.rng.randint(3, 14)
                policy = self.rng.choice(policies)

                rules.append({
                    "rule_id": f"{RPL_PREFIX}-{rule_idx:06d}",
                    "sku_id": sku["sku_id"],
                    "location_id": loc["location_id"],
                    "minimum_stock": safety,
                    "maximum_stock": max_stock,
                    "reorder_point": reorder_pt,
                    "safety_stock": safety,
                    "lead_time_days": lead_time,
                    "reorder_quantity": reorder_qty,
                    "inbound_eligibility_policy": policy,
                    "effective_from": self.base_date,
                    "effective_to": None,
                    "is_active": True
                })
                rule_idx += 1
        return rules

    # 5. Opening Balances and Movements Generator (Chunked & Streaming)
    def generate_movements_chunked(
        self,
        target_movements: int,
        skus: List[Dict[str, Any]],
        locations: List[Dict[str, Any]],
        chunk_size: int = 50000
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Generates movements in deterministic chunks without blowing memory.
        First generates OPENING_BALANCE for every SKU/Location combination,
        then subsequent realistic movements.
        """
        sku_ids = [s["sku_id"] for s in skus]
        loc_ids = [l["location_id"] for l in locations]
        m_types, m_weights = zip(*MOVEMENT_TYPES)

        current_mov_id = 1
        year = 2026
        buffer = []

        # 1. Opening balances
        for loc_id in loc_ids:
            for sku_id in sku_ids:
                if current_mov_id > target_movements:
                    break
                qty = self.rng.randint(100, 1000)
                buffer.append({
                    "movement_id": f"{MOV_PREFIX}-{year}-{current_mov_id:08d}",
                    "sku_id": sku_id,
                    "source_location_id": None,
                    "destination_location_id": loc_id,
                    "movement_type": "OPENING_BALANCE",
                    "quantity": qty,
                    "reference_type": "SYSTEM_INITIALIZATION",
                    "reference_id": f"INIT-{loc_id}",
                    "transfer_id": None,
                    "occurred_at": self.base_date,
                    "recorded_at": self.base_date,
                    "reason_code": "OPENING_STOCK",
                    "created_by": "DATA_ENGINE",
                    "metadata_json": '{"channel": "ALL"}'
                })
                current_mov_id += 1
                if len(buffer) >= chunk_size:
                    yield buffer
                    buffer = []

        # 2. Subsequent movements up to target_movements
        total_remaining = target_movements - current_mov_id + 1
        time_step_seconds = max(1, int(180 * 86400 / max(1, target_movements)))

        current_time = self.base_date
        for _ in range(total_remaining):
            current_time += datetime.timedelta(seconds=time_step_seconds)
            m_type = self.rng.choices(m_types, weights=m_weights)[0]
            sku_id = self.rng.choice(sku_ids)
            qty = self.rng.randint(1, 40)

            src_loc = None
            dest_loc = None
            transfer_id = None
            ref_type = "OPERATIONAL"

            if m_type in ["RECEIPT", "ADJUSTMENT_IN", "CUSTOMER_RETURN"]:
                dest_loc = self.rng.choice(loc_ids)
                ref_type = "PURCHASE_ORDER" if m_type == "RECEIPT" else "INVENTORY_ADJUSTMENT"
            elif m_type in ["SALE", "ADJUSTMENT_OUT", "DAMAGE"]:
                src_loc = self.rng.choice(loc_ids)
                ref_type = "CUSTOMER_SALE" if m_type == "SALE" else "INVENTORY_ADJUSTMENT"
            elif m_type == "TRANSFER_DISPATCH":
                src_loc = self.rng.choice(loc_ids)
                dest_candidates = [l for l in loc_ids if l != src_loc]
                dest_loc = self.rng.choice(dest_candidates) if dest_candidates else src_loc
                transfer_id = f"{TRN_PREFIX}-{year}-{self.rng.randint(1, 1000):06d}"
                ref_type = "TRANSFER"
            elif m_type == "TRANSFER_RECEIPT":
                dest_loc = self.rng.choice(loc_ids)
                src_candidates = [l for l in loc_ids if l != dest_loc]
                src_loc = self.rng.choice(src_candidates) if src_candidates else dest_loc
                transfer_id = f"{TRN_PREFIX}-{year}-{self.rng.randint(1, 1000):06d}"
                ref_type = "TRANSFER"
            elif m_type in ["BLOCK", "UNBLOCK"]:
                dest_loc = self.rng.choice(loc_ids)
                ref_type = "QUALITY_HOLD"

            buffer.append({
                "movement_id": f"{MOV_PREFIX}-{year}-{current_mov_id:08d}",
                "sku_id": sku_id,
                "source_location_id": src_loc,
                "destination_location_id": dest_loc,
                "movement_type": m_type,
                "quantity": qty,
                "reference_type": ref_type,
                "reference_id": f"REF-{current_mov_id:08d}",
                "transfer_id": transfer_id,
                "occurred_at": current_time,
                "recorded_at": current_time,
                "reason_code": f"CYCLE_{m_type}",
                "created_by": "DATA_ENGINE",
                "metadata_json": '{"automated": true}'
            })
            current_mov_id += 1
            if len(buffer) >= chunk_size:
                yield buffer
                buffer = []

        if buffer:
            yield buffer

    # 6. Orders & Lines Generator
    def generate_orders_and_lines(
        self,
        order_count: int,
        skus: List[Dict[str, Any]],
        locations: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        orders = []
        order_lines = []
        channels = ["ONLINE", "RETAIL", "MARKETPLACE", "B2B"]
        channel_weights = [0.55, 0.20, 0.15, 0.10]
        sku_ids = [s["sku_id"] for s in skus]
        sku_price_map = {s["sku_id"]: s["selling_price"] for s in skus}
        loc_ids = [l["location_id"] for l in locations]
        year = 2026

        current_time = self.base_date + datetime.timedelta(days=1)
        for i in range(1, order_count + 1):
            order_id = f"{ORD_PREFIX}-{year}-{i:06d}"
            channel = self.rng.choices(channels, weights=channel_weights)[0]
            cust_ref = f"CUST-SYN-{self.rng.randint(10000, 99999)}"
            order_date = current_time + datetime.timedelta(minutes=i * 20)
            req_delivery = order_date + datetime.timedelta(days=self.rng.randint(2, 7))
            fulfillment_loc = self.rng.choice(loc_ids)

            num_lines = self.rng.choices([1, 2, 3, 4], weights=[0.55, 0.25, 0.15, 0.05])[0]
            chosen_skus = self.rng.sample(sku_ids, k=min(num_lines, len(sku_ids)))
            total_amount = 0.0

            for line_idx, sku_id in enumerate(chosen_skus, start=1):
                line_id = f"ORDL-{year}-{i:06d}-{line_idx:02d}"
                qty = self.rng.choices([1, 2, 3, 5, 10], weights=[0.60, 0.20, 0.10, 0.07, 0.03])[0]
                price = float(sku_price_map[sku_id])
                total_amount += (qty * price)

                order_lines.append({
                    "order_line_id": line_id,
                    "order_id": order_id,
                    "sku_id": sku_id,
                    "ordered_quantity": qty,
                    "allocated_quantity": qty,  # baseline allocated
                    "fulfilled_quantity": qty,
                    "unit_price": price,
                    "line_status": "FULFILLED"
                })

            orders.append({
                "order_id": order_id,
                "channel": channel,
                "customer_reference": cust_ref,
                "order_status": "SHIPPED",
                "order_date": order_date,
                "requested_delivery_date": req_delivery,
                "fulfillment_location_id": fulfillment_loc,
                "total_amount": round(total_amount, 2),
                "currency": "USD",
                "created_at": order_date
            })

        return orders, order_lines

    # 7. Injected Anomalies and Ground Truth Generation (All 4 Required Scenarios)
    def generate_anomalies_and_ground_truth(
        self,
        skus: List[Dict[str, Any]],
        locations: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Creates isolated ground-truth records and synthetic injection instructions
        for all 4 mandatory anomalies with scaled enterprise test cases:
          1. BALANCE_MISMATCH
          2. RESERVATION_OVERFLOW
          3. BLOCKED_STOCK_FULFILLMENT
          4. PREMATURE_TRANSFER
        """
        ground_truth_records = []
        injected_anomalies = []
        now = datetime.datetime.utcnow()

        # Scale anomaly count based on dataset size: 4 per type for full profile, 2 for starter
        per_type = 4 if len(skus) >= 1000 else 2
        benign_target = 100 if len(skus) >= 1000 else 20

        # Anomaly 1: Balance Mismatch
        for k in range(per_type):
            sku_k = skus[k]["sku_id"]
            loc_k = locations[k % len(locations)]["location_id"]
            drift = 75 + (k * 25)
            gt = {
                "scenario_id": f"SCENARIO_001_BALANCE_MISMATCH_{k+1:02d}",
                "entity_id": f"BAL-{sku_k}-{loc_k}",
                "entity_type": "InventoryBalance",
                "issue_type": "BALANCE_MISMATCH",
                "is_anomaly": True,
                "expected_decision": "FLAG_RECONCILIATION_EXCEPTION",
                "expected_calculation": f"Stored balance drifts by +{drift} units from movement ledger",
                "explanation": f"Simulated network dropped transaction #{k+1} causing projected balance to exceed immutable movements."
            }
            ground_truth_records.append(gt)
            injected_anomalies.append({
                "type": "BALANCE_MISMATCH",
                "sku_id": sku_k,
                "location_id": loc_k,
                "drift_units": drift
            })

        # Anomaly 2: Reservation Overflow
        offset_2 = per_type
        for k in range(per_type):
            sku_k = skus[offset_2 + k]["sku_id"] if len(skus) > offset_2 + k else skus[0]["sku_id"]
            loc_k = locations[(offset_2 + k) % len(locations)]["location_id"]
            gt = {
                "scenario_id": f"SCENARIO_002_RESERVATION_OVERFLOW_{k+1:02d}",
                "entity_id": f"{sku_k}:{loc_k}",
                "entity_type": "ReservationGroup",
                "issue_type": "RESERVATION_OVERFLOW",
                "is_anomaly": True,
                "expected_decision": "REJECT_OR_FLAG_RESERVATION",
                "expected_calculation": f"Active reservations exceed physical reservable stock by 50,000 units",
                "explanation": f"Simulated concurrent race condition #{k+1} overselling available inventory."
            }
            ground_truth_records.append(gt)
            injected_anomalies.append({
                "type": "RESERVATION_OVERFLOW",
                "sku_id": sku_k,
                "location_id": loc_k,
                "oversell_units": 50000
            })

        # Anomaly 3: Blocked Stock Fulfillment
        offset_3 = per_type * 2
        for k in range(per_type):
            sku_k = skus[offset_3 + k]["sku_id"] if len(skus) > offset_3 + k else skus[0]["sku_id"]
            loc_k = locations[(offset_3 + k) % len(locations)]["location_id"]
            alc_id = f"ALC-INJECTED-BLOCKED-{sku_k}"
            gt = {
                "scenario_id": f"SCENARIO_003_BLOCKED_STOCK_FULFILLMENT_{k+1:02d}",
                "entity_id": alc_id,
                "entity_type": "Allocation",
                "issue_type": "BLOCKED_STOCK_FULFILLMENT",
                "is_anomaly": True,
                "expected_decision": "REJECT_FULFILLMENT",
                "expected_calculation": "Allocation quantity assigned against quarantined/damaged lot",
                "explanation": f"Operator bypassed ATP validation and allocated blocked inventory case #{k+1}."
            }
            ground_truth_records.append(gt)
            injected_anomalies.append({
                "type": "BLOCKED_STOCK_FULFILLMENT",
                "entity_id": alc_id,
                "sku_id": sku_k,
                "location_id": loc_k,
                "blocked_units": 100,
                "allocated_units": 20
            })

        # Anomaly 4: Premature Transfer Double Counting
        offset_4 = per_type * 3
        for k in range(per_type):
            sku_k = skus[offset_4 + k]["sku_id"] if len(skus) > offset_4 + k else skus[0]["sku_id"]
            src_k = locations[k % len(locations)]["location_id"]
            dest_k = locations[(k + 1) % len(locations)]["location_id"] if len(locations) > 1 else src_k
            trn_id = f"TRN-INJECTED-PREMATURE-{k+1:02d}"
            gt = {
                "scenario_id": f"SCENARIO_004_PREMATURE_TRANSFER_{k+1:02d}",
                "entity_id": trn_id,
                "entity_type": "Transfer",
                "issue_type": "PREMATURE_TRANSFER",
                "is_anomaly": True,
                "expected_decision": "FLAG_TRANSFER_ACCOUNTING_EXCEPTION",
                "expected_calculation": "Destination credited before physical dispatch; double counted",
                "explanation": f"Inbound scanner checked in shipment #{k+1} without outbound dispatch confirmation."
            }
            ground_truth_records.append(gt)
            injected_anomalies.append({
                "type": "PREMATURE_TRANSFER",
                "transfer_id": trn_id,
                "source_location_id": src_k,
                "destination_location_id": dest_k,
                "sku_id": sku_k,
                "quantity": 50
            })

        # Add benign normal operations to verify Precision/Recall
        benign_start = per_type * 4
        benign_end = min(len(skus), benign_start + benign_target)
        for i in range(benign_start, benign_end):
            s_id = skus[i]["sku_id"]
            l_id = locations[i % len(locations)]["location_id"]
            ground_truth_records.append({
                "scenario_id": f"BENIGN_NORMAL_OPERATION_{i:04d}",
                "entity_id": f"BAL-{s_id}-{l_id}",
                "entity_type": "InventoryBalance",
                "issue_type": "NONE",
                "is_anomaly": False,
                "expected_decision": "ACCEPT",
                "expected_calculation": "Ledger on-hand equals stored balance exactly",
                "explanation": "Standard balanced ledger transaction with full reconciliation."
            })

        scenario_manifest = {
            "generation_seed": self.seed,
            "generated_at": now.isoformat(),
            "total_scenarios": len(ground_truth_records),
            "anomaly_scenarios": len(injected_anomalies),
            "benign_scenarios": len(ground_truth_records) - len(injected_anomalies),
            "scenarios": ground_truth_records
        }

        return ground_truth_records, injected_anomalies, scenario_manifest
