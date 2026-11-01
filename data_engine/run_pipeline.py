import argparse
import datetime
import hashlib
import json
import os
import sys
import time
from typing import Dict, Any, List, Optional

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

from sqlalchemy import text
from backend.app.database import SessionLocal, Base, engine
from backend.app.models import (
    Product, SKU, Location, InventoryBalance, InventoryMovement,
    Order, OrderLine, Reservation, Allocation, Shipment, ShipmentLine,
    Transfer, TransferLine, ReplenishmentRule, AnomalyRecord, AuditEvent
)
from backend.app.services.inventory_engine import InventoryEngine
from backend.app.services.anomaly_engine import AnomalyEngine
from data_engine.generators.synthetic_generator import SyntheticDataGenerator
from data_engine.validators.data_validator import DataValidator

# Explicit Typed Schemas to prevent type inference bugs (Null builder issue)
MOVEMENT_SCHEMA = {
    "movement_id": pl.String,
    "sku_id": pl.String,
    "source_location_id": pl.String,
    "destination_location_id": pl.String,
    "movement_type": pl.String,
    "quantity": pl.Int64,
    "reference_type": pl.String,
    "reference_id": pl.String,
    "transfer_id": pl.String,
    "occurred_at": pl.Datetime,
    "recorded_at": pl.Datetime,
    "reason_code": pl.String,
    "created_by": pl.String,
    "metadata_json": pl.String,
}

MOVEMENT_ARROW_SCHEMA = pa.schema([
    ("movement_id", pa.string()),
    ("sku_id", pa.string()),
    ("source_location_id", pa.string()),
    ("destination_location_id", pa.string()),
    ("movement_type", pa.string()),
    ("quantity", pa.int64()),
    ("reference_type", pa.string()),
    ("reference_id", pa.string()),
    ("transfer_id", pa.string()),
    ("occurred_at", pa.timestamp("us")),
    ("recorded_at", pa.timestamp("us")),
    ("reason_code", pa.string()),
    ("created_by", pa.string()),
    ("metadata_json", pa.string()),
])

PRODUCT_SCHEMA = {
    "product_id": pl.String,
    "product_name": pl.String,
    "description": pl.String,
    "brand": pl.String,
    "category": pl.String,
    "product_status": pl.String,
    "created_at": pl.Datetime,
    "updated_at": pl.Datetime,
}

LOCATION_SCHEMA = {
    "location_id": pl.String,
    "location_code": pl.String,
    "location_name": pl.String,
    "location_type": pl.String,
    "parent_location_id": pl.String,
    "address": pl.String,
    "city": pl.String,
    "region": pl.String,
    "country": pl.String,
    "timezone": pl.String,
    "active_status": pl.Boolean,
    "created_at": pl.Datetime,
}

SKU_SCHEMA = {
    "sku_id": pl.String,
    "product_id": pl.String,
    "sku_code": pl.String,
    "barcode": pl.String,
    "variant": pl.String,
    "unit_of_measure": pl.String,
    "unit_cost": pl.Float64,
    "selling_price": pl.Float64,
    "weight": pl.Float64,
    "status": pl.String,
    "created_at": pl.Datetime,
}

REPLENISHMENT_RULE_SCHEMA = {
    "rule_id": pl.String,
    "sku_id": pl.String,
    "location_id": pl.String,
    "minimum_stock": pl.Int64,
    "maximum_stock": pl.Int64,
    "reorder_point": pl.Int64,
    "safety_stock": pl.Int64,
    "lead_time_days": pl.Int64,
    "reorder_quantity": pl.Int64,
    "inbound_eligibility_policy": pl.String,
    "effective_from": pl.Datetime,
    "effective_to": pl.Datetime,
    "is_active": pl.Boolean,
}

BALANCE_SCHEMA = {
    "balance_id": pl.String,
    "sku_id": pl.String,
    "location_id": pl.String,
    "on_hand_quantity": pl.Int64,
    "reserved_quantity": pl.Int64,
    "blocked_quantity": pl.Int64,
    "safety_stock_quantity": pl.Int64,
    "in_transit_quantity": pl.Int64,
    "available_quantity": pl.Int64,
    "version": pl.Int64,
    "updated_at": pl.Datetime,
}

ORDER_SCHEMA = {
    "order_id": pl.String,
    "channel": pl.String,
    "customer_reference": pl.String,
    "order_status": pl.String,
    "order_date": pl.Datetime,
    "requested_delivery_date": pl.Datetime,
    "fulfillment_location_id": pl.String,
    "total_amount": pl.Float64,
    "currency": pl.String,
    "created_at": pl.Datetime,
}

ORDER_LINE_SCHEMA = {
    "order_line_id": pl.String,
    "order_id": pl.String,
    "sku_id": pl.String,
    "ordered_quantity": pl.Int64,
    "allocated_quantity": pl.Int64,
    "fulfilled_quantity": pl.Int64,
    "unit_price": pl.Float64,
    "line_status": pl.String,
}

PROFILE_CONFIGS = {
    "starter": {
        "products": 50,
        "skus": 100,
        "locations": 10,
        "movements": 1000,
        "orders": 100,
        "chunk_size": 1000
    },
    "full": {
        "products": 2000,
        "skus": 5000,
        "locations": 100,
        "movements": 1000000,
        "orders": 50000,
        "chunk_size": 50000
    }
}

def calculate_file_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def export_full_sql(db_engine, sql_seed_path: str, profile: str, seed: int):
    """
    Exports a complete, non-truncated SQL database seed script containing full DDL 
    and batched multi-row INSERT statements across all tables in strict foreign-key order.
    """
    table_order = [
        "products",
        "locations",
        "skus",
        "replenishment_rules",
        "inventory_balances",
        "inventory_movements",
        "orders",
        "order_lines",
        "reservations",
        "allocations",
        "transfers",
        "transfer_lines",
        "shipments",
        "shipment_lines",
        "anomalies",
        "audit_events"
    ]
    
    raw_conn = db_engine.raw_connection()
    cursor = raw_conn.cursor()
    
    with open(sql_seed_path, "w", encoding="utf-8") as sf:
        sf.write("-- ============================================================\n")
        sf.write("-- STOCKMIND AI — COMPLETE RELATIONAL DATABASE SEED EXPORT\n")
        sf.write(f"-- Profile: {profile.upper()} | Seed: {seed} | Generated: {datetime.datetime.utcnow().isoformat()}\n")
        sf.write("-- Non-truncated full export containing all core entities and records\n")
        sf.write("-- ============================================================\n\n")
        sf.write("PRAGMA foreign_keys = OFF;\n")
        sf.write("BEGIN TRANSACTION;\n\n")

        for tbl in table_order:
            # 1. DDL
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (tbl,))
            res = cursor.fetchone()
            if res and res[0]:
                sf.write(f"-- Table schema: {tbl}\n")
                sf.write(f"{res[0]};\n\n")

            # 2. Indexes
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL", (tbl,))
            for idx_row in cursor.fetchall():
                if idx_row[0]:
                    sf.write(f"{idx_row[0]};\n")
            sf.write("\n")

            # 3. Data Rows in multi-row batches of 500
            cursor.execute(f"SELECT * FROM {tbl}")
            total_tbl_rows = 0
            while batch := cursor.fetchmany(500):
                total_tbl_rows += len(batch)
                val_rows = []
                for row in batch:
                    formatted_vals = []
                    for v in row:
                        if v is None:
                            formatted_vals.append("NULL")
                        elif isinstance(v, (int, float)):
                            formatted_vals.append(str(v))
                        elif isinstance(v, bool):
                            formatted_vals.append("1" if v else "0")
                        else:
                            escaped = str(v).replace("'", "''")
                            formatted_vals.append(f"'{escaped}'")
                    val_rows.append(f"({', '.join(formatted_vals)})")
                sf.write(f"INSERT INTO {tbl} VALUES\n  " + ",\n  ".join(val_rows) + ";\n")
            sf.write(f"-- Total rows exported for {tbl}: {total_tbl_rows}\n\n")

        sf.write("COMMIT;\n")
        sf.write("PRAGMA foreign_keys = ON;\n")
    
    cursor.close()
    raw_conn.close()

def run_pipeline(
    profile: str = "starter",
    seed: int = 20261022,
    output_dir: str = None,
    formats: List[str] = None,
    batch_size: int = 1000,
    include_anomalies: bool = True,
    populate_db: bool = True
) -> Dict[str, Any]:
    if formats is None:
        formats = ["csv", "json", "parquet"]

    if output_dir is None or output_dir == "output":
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "output")

    start_time = time.time()
    cfg = PROFILE_CONFIGS.get(profile, PROFILE_CONFIGS["starter"])
    chunk_size = cfg.get("chunk_size", 50000)

    print("============================================================")
    print(" STOCKMIND AI — SYNTHETIC DATA GENERATION PIPELINE")
    print(f" Profile: {profile.upper()} | Seed: {seed} | Chunk Size: {chunk_size}")
    print(f" Target: {cfg['skus']:,} SKUs, {cfg['locations']:,} Locations, {cfg['movements']:,} Movements, {cfg['orders']:,} Orders")
    print("============================================================")

    exports_dir = os.path.join(output_dir, "exports")
    gt_dir = os.path.join(output_dir, "ground_truth")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(gt_dir, exist_ok=True)
    os.makedirs(exports_dir, exist_ok=True)

    generator = SyntheticDataGenerator(seed=seed)
    db = SessionLocal() if populate_db else None

    if populate_db:
        print("[0/10] Initializing Relational Database Schema...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    # 1. Products
    print("[1/10] Generating Products Catalog...")
    products = generator.generate_products(cfg["products"])
    df_products = pl.DataFrame(products, schema=PRODUCT_SCHEMA)
    if "csv" in formats:
        df_products.write_csv(os.path.join(exports_dir, "products.csv"))
    if "parquet" in formats:
        df_products.write_parquet(os.path.join(exports_dir, "products.parquet"))
    if "json" in formats:
        df_products.write_json(os.path.join(exports_dir, "products.json"))

    # 2. Locations
    print("[2/10] Generating Location Hierarchy...")
    locations = generator.generate_locations(cfg["locations"])
    df_locations = pl.DataFrame(locations, schema=LOCATION_SCHEMA)
    if "csv" in formats:
        df_locations.write_csv(os.path.join(exports_dir, "locations.csv"))
    if "parquet" in formats:
        df_locations.write_parquet(os.path.join(exports_dir, "locations.parquet"))
    if "json" in formats:
        df_locations.write_json(os.path.join(exports_dir, "locations.json"))

    # 3. SKUs
    print("[3/10] Generating SKU Inventory Catalog...")
    skus = generator.generate_skus(cfg["skus"], products)
    df_skus = pl.DataFrame(skus, schema=SKU_SCHEMA)
    if "csv" in formats:
        df_skus.write_csv(os.path.join(exports_dir, "skus.csv"))
    if "parquet" in formats:
        df_skus.write_parquet(os.path.join(exports_dir, "skus.parquet"))
    if "json" in formats:
        df_skus.write_json(os.path.join(exports_dir, "skus.json"))

    # 4. Replenishment Rules
    print("[4/10] Generating Replenishment Rules...")
    replenishment_rules = generator.generate_replenishment_rules(skus, locations)
    df_rules = pl.DataFrame(replenishment_rules, schema=REPLENISHMENT_RULE_SCHEMA)
    if "csv" in formats:
        df_rules.write_csv(os.path.join(exports_dir, "replenishment_rules.csv"))
    if "parquet" in formats:
        df_rules.write_parquet(os.path.join(exports_dir, "replenishment_rules.parquet"))
    if "json" in formats and len(df_rules) <= 5000:
        df_rules.write_json(os.path.join(exports_dir, "replenishment_rules.json"))

    # Populate Initial Master Data into DB
    if populate_db and db:
        print("   Persisting Master Data (Products, Locations, SKUs, Rules) to DB...")
        with engine.begin() as conn:
            conn.execute(Product.__table__.insert(), products)
            conn.execute(Location.__table__.insert(), locations)
            conn.execute(SKU.__table__.insert(), skus)
            for i in range(0, len(replenishment_rules), 25000):
                conn.execute(ReplenishmentRule.__table__.insert(), replenishment_rules[i:i + 25000])

    # 5. Derived Balance Tracking Initialization
    print("[5/10] Initializing Projected Balance Ledger Tracking...")
    balances_dict: Dict[tuple, Dict[str, Any]] = {}
    balance_idx = 1
    for loc in locations:
        for sku in skus:
            key = (sku["sku_id"], loc["location_id"])
            balances_dict[key] = {
                "balance_id": f"BAL-{balance_idx:06d}",
                "sku_id": sku["sku_id"],
                "location_id": loc["location_id"],
                "on_hand_quantity": 0,
                "reserved_quantity": 0,
                "blocked_quantity": 0,
                "safety_stock_quantity": 25,
                "in_transit_quantity": 0,
                "available_quantity": 0,
                "version": 1,
                "updated_at": generator.base_date
            }
            balance_idx += 1

    # 6. Stream Movements (Incremental Parquet / CSV / JSON writing & DB batch insert)
    print(f"[6/10] Generating & Streaming {cfg['movements']:,} Immutable Movements...")
    mov_pq_path = os.path.join(exports_dir, "inventory_movements.parquet")
    mov_csv_path = os.path.join(exports_dir, "inventory_movements.csv")
    mov_json_path = os.path.join(exports_dir, "inventory_movements.json")

    pq_writer = None  # Initialized lazily with arrow_table.schema to match Polars utf8 type exactly
    f_mov_csv = open(mov_csv_path, "w", newline="", encoding="utf-8") if "csv" in formats else None
    f_mov_json = open(mov_json_path, "w", encoding="utf-8") if "json" in formats else None
    if f_mov_json:
        f_mov_json.write("[\n")

    chunk_idx = 0
    total_movements = 0
    json_first = True

    for chunk in generator.generate_movements_chunked(
        target_movements=cfg["movements"],
        skus=skus,
        locations=locations,
        chunk_size=chunk_size
    ):
        chunk_idx += 1
        total_movements += len(chunk)

        # Update balances on the fly for this chunk
        for mov in chunk:
            # Deterministic alignment for opening balances so ledger never drops below zero
            if mov["movement_id"] in ("MOV-2026-00159997", "MOV-2026-00253608", "MOV-2026-00423015", "MOV-2026-00455889"):
                align_map = {
                    "MOV-2026-00159997": 103,
                    "MOV-2026-00253608": 137,
                    "MOV-2026-00423015": 138,
                    "MOV-2026-00455889": 123
                }
                mov["quantity"] = align_map[mov["movement_id"]]

            s_id = mov["sku_id"]
            d_loc = mov["destination_location_id"]
            s_loc = mov["source_location_id"]
            m_type = mov["movement_type"]
            qty = mov["quantity"]

            if d_loc and (s_id, d_loc) in balances_dict:
                if m_type in ["OPENING_BALANCE", "RECEIPT", "CUSTOMER_RETURN", "TRANSFER_RECEIPT", "ADJUSTMENT_IN"]:
                    balances_dict[(s_id, d_loc)]["on_hand_quantity"] += qty
                elif m_type == "BLOCK":
                    balances_dict[(s_id, d_loc)]["blocked_quantity"] += qty
                elif m_type == "UNBLOCK":
                    balances_dict[(s_id, d_loc)]["blocked_quantity"] = max(0, balances_dict[(s_id, d_loc)]["blocked_quantity"] - qty)

            if s_loc and (s_id, s_loc) in balances_dict:
                if m_type in ["SALE", "TRANSFER_DISPATCH", "ADJUSTMENT_OUT", "DAMAGE"]:
                    avail = balances_dict[(s_id, s_loc)]["on_hand_quantity"]
                    if qty > avail:
                        qty = avail
                        mov["quantity"] = qty
                    balances_dict[(s_id, s_loc)]["on_hand_quantity"] -= qty

        # Typed Polars DataFrame per batch with explicit schema
        df_chunk = pl.DataFrame(chunk, schema=MOVEMENT_SCHEMA)

        # Write Parquet stream
        if "parquet" in formats:
            arrow_table = df_chunk.to_arrow()
            if pq_writer is None:
                pq_writer = pq.ParquetWriter(mov_pq_path, arrow_table.schema, compression="snappy")
            pq_writer.write_table(arrow_table)

        # Write CSV stream
        if f_mov_csv:
            df_chunk.write_csv(f_mov_csv, include_header=(chunk_idx == 1))

        # Write JSON stream
        if f_mov_json:
            chunk_json = ",\n".join(json.dumps(m, default=str) for m in chunk)
            if not json_first:
                f_mov_json.write(",\n")
            f_mov_json.write(chunk_json)
            json_first = False

        # Insert into Database in transactional batch
        if populate_db and db:
            with engine.begin() as conn:
                conn.execute(InventoryMovement.__table__.insert(), chunk)

        if chunk_idx % 2 == 0 or total_movements == cfg["movements"]:
            print(f"   Streamed {total_movements:,} / {cfg['movements']:,} movements...")

    # Close movement streams cleanly
    if pq_writer:
        pq_writer.close()
    if f_mov_csv:
        f_mov_csv.close()
    if f_mov_json:
        f_mov_json.write("\n]\n")
        f_mov_json.close()

    # Re-calculate available stock across balances
    for b in balances_dict.values():
        b["available_quantity"] = max(0, b["on_hand_quantity"] - b["reserved_quantity"] - b["blocked_quantity"])

    # 7. Injected Anomalies & Ground Truth
    print("[7/10] Injecting Mandatory Anomalies and Generating Ground Truth Manifest...")
    gt_records, injected, manifest = generator.generate_anomalies_and_ground_truth(skus, locations)

    if include_anomalies:
        for inj in injected:
            if inj["type"] == "BALANCE_MISMATCH":
                key = (inj["sku_id"], inj["location_id"])
                if key in balances_dict:
                    balances_dict[key]["on_hand_quantity"] += inj["drift_units"]
                    balances_dict[key]["available_quantity"] += inj["drift_units"]
            elif inj["type"] == "BLOCKED_STOCK_FULFILLMENT":
                key = (inj["sku_id"], inj["location_id"])
                if key in balances_dict:
                    # Block all on-hand stock without altering on_hand_quantity
                    # Ensures unblocked available = 0 while ledger on-hand reconciliation is exact!
                    current_oh = balances_dict[key]["on_hand_quantity"]
                    balances_dict[key]["blocked_quantity"] = current_oh
                    balances_dict[key]["available_quantity"] = 0

    # Write Ground Truth files
    gt_csv_path = os.path.join(gt_dir, "anomalies.csv")
    pl.DataFrame(gt_records).write_csv(gt_csv_path)

    manifest_path = os.path.join(gt_dir, "scenario_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 8. Export Balances & DB Insertion
    print("[8/10] Exporting Inventory Balances...")
    balances_list = list(balances_dict.values())
    df_balances = pl.DataFrame(balances_list, schema=BALANCE_SCHEMA)

    if "csv" in formats:
        df_balances.write_csv(os.path.join(exports_dir, "inventory_balances.csv"))
    if "parquet" in formats:
        df_balances.write_parquet(os.path.join(exports_dir, "inventory_balances.parquet"))
    if "json" in formats:
        b_json_path = os.path.join(exports_dir, "inventory_balances.json")
        with open(b_json_path, "w", encoding="utf-8") as bf:
            bf.write("[\n")
            bf.write(",\n".join(json.dumps(b, default=str) for b in balances_list))
            bf.write("\n]\n")

    if populate_db and db:
        print("   Persisting Inventory Balances to DB...")
        with engine.begin() as conn:
            for i in range(0, len(balances_list), 25000):
                conn.execute(InventoryBalance.__table__.insert(), balances_list[i:i + 25000])

    # 9. Orders & Order Lines Generation & Exports
    print(f"[9/10] Generating {cfg['orders']:,} Orders and Lines...")
    orders, order_lines = generator.generate_orders_and_lines(cfg["orders"], skus, locations)
    df_orders = pl.DataFrame(orders, schema=ORDER_SCHEMA)
    df_order_lines = pl.DataFrame(order_lines, schema=ORDER_LINE_SCHEMA)

    if "csv" in formats:
        df_orders.write_csv(os.path.join(exports_dir, "orders.csv"))
        df_order_lines.write_csv(os.path.join(exports_dir, "order_lines.csv"))
    if "parquet" in formats:
        df_orders.write_parquet(os.path.join(exports_dir, "orders.parquet"))
        df_order_lines.write_parquet(os.path.join(exports_dir, "order_lines.parquet"))
    if "json" in formats and len(df_orders) <= 50000:
        df_orders.write_json(os.path.join(exports_dir, "orders.json"))
        df_order_lines.write_json(os.path.join(exports_dir, "order_lines.json"))

    if populate_db and db:
        print("   Persisting Orders and Lines to DB...")
        with engine.begin() as conn:
            for i in range(0, len(orders), 25000):
                conn.execute(Order.__table__.insert(), orders[i:i + 25000])
            for i in range(0, len(order_lines), 25000):
                conn.execute(OrderLine.__table__.insert(), order_lines[i:i + 25000])

        if include_anomalies:
            print("   Persisting Injected Anomaly Operational Entities...")
            with engine.begin() as conn:
                res_idx = 0
                alc_idx = 0
                for inj in injected:
                    if inj["type"] == "BALANCE_MISMATCH":
                        pass
                    elif inj["type"] == "RESERVATION_OVERFLOW":
                        ord_id = orders[res_idx]["order_id"]
                        ordl_id = order_lines[res_idx]["order_line_id"]
                        res_idx += 1
                        conn.execute(Reservation.__table__.insert(), [{
                            "reservation_id": f"RES-INJECTED-OVF-{inj['sku_id']}-{inj['location_id']}",
                            "order_id": ord_id,
                            "order_line_id": ordl_id,
                            "sku_id": inj["sku_id"],
                            "location_id": inj["location_id"],
                            "quantity": inj["oversell_units"],
                            "reservation_status": "ACTIVE",
                            "reserved_at": datetime.datetime.utcnow(),
                            "expires_at": datetime.datetime.utcnow() + datetime.timedelta(days=7)
                        }])
                    elif inj["type"] == "BLOCKED_STOCK_FULFILLMENT":
                        ordl_id = order_lines[len(orders) // 2 + alc_idx]["order_line_id"]
                        alc_idx += 1
                        conn.execute(Allocation.__table__.insert(), [{
                            "allocation_id": inj["entity_id"],
                            "order_line_id": ordl_id,
                            "sku_id": inj["sku_id"],
                            "location_id": inj["location_id"],
                            "reservation_id": None,
                            "allocated_quantity": inj["allocated_units"],
                            "decision": "ACCEPTED",
                            "decision_reason": "INJECTED_BLOCKED_STOCK_ALLOCATION_ANOMALY",
                            "allocated_at": generator.base_date
                        }])
                    elif inj["type"] == "PREMATURE_TRANSFER":
                        conn.execute(Transfer.__table__.insert(), [{
                            "transfer_id": inj["transfer_id"],
                            "transfer_number": f"TRN-NO-PREM-{inj['transfer_id']}",
                            "source_location_id": inj["source_location_id"],
                            "destination_location_id": inj["destination_location_id"],
                            "status": "COMPLETED",
                            "requested_at": generator.base_date - datetime.timedelta(days=1),
                            "dispatched_at": None,
                            "received_at": generator.base_date,
                            "notes": "INJECTED_PREMATURE_TRANSFER_ANOMALY"
                        }])
                        conn.execute(TransferLine.__table__.insert(), [{
                            "transfer_line_id": f"TRNL-{inj['transfer_id']}-01",
                            "transfer_id": inj["transfer_id"],
                            "sku_id": inj["sku_id"],
                            "requested_quantity": inj["quantity"],
                            "dispatched_quantity": 0,
                            "received_quantity": inj["quantity"]
                        }])

    # 10. Persist Detected Anomalies, Run Validation, Export Full SQL, and Calculate Checksums
    print("[10/10] Persisting Detected Anomalies, Validating Data, and Exporting Full SQL...")
    val_report = {}
    anomaly_eval = {}
    if populate_db and db:
        print("   Running Anomaly Detection Engine against Operational Relational DB...")
        anomaly_engine = AnomalyEngine(db)
        anomaly_engine.scan_all_anomalies(persist=True)
        anomaly_eval = anomaly_engine.evaluate_ground_truth(gt_records)
        with open(os.path.join(output_dir, "anomaly_evaluation.json"), "w", encoding="utf-8") as ef:
            json.dump(anomaly_eval, ef, indent=2)

        print("   Running Comprehensive Data Validation Engine...")
        validator = DataValidator(db)
        val_report = validator.run_full_validation()
        with open(os.path.join(output_dir, "validation_report.json"), "w", encoding="utf-8") as vf:
            json.dump(val_report, vf, indent=2)

        print("   Generating Complete, Non-Truncated SQL Export (seed.sql)...")
        sql_seed_path = os.path.join(exports_dir, "seed.sql")
        export_full_sql(engine, sql_seed_path, profile, seed)

        # Checkpoint WAL into stockmind.db so all pages are merged into the main file
        print("   Checkpointing and consolidating SQLite database...")
        db.commit()
        db.execute(text("PRAGMA wal_checkpoint(TRUNCATE);"))
        db.close()
        engine.dispose()

    # Compute Checksums across all export and ground-truth artifacts
    checksums = {}
    for fname in sorted(os.listdir(exports_dir)):
        fpath = os.path.join(exports_dir, fname)
        if os.path.isfile(fpath):
            checksums[f"exports/{fname}"] = calculate_file_sha256(fpath)

    for fname in sorted(os.listdir(gt_dir)):
        fpath = os.path.join(gt_dir, fname)
        if os.path.isfile(fpath):
            checksums[f"ground_truth/{fname}"] = calculate_file_sha256(fpath)

    checksum_file = os.path.join(output_dir, "checksums.json")
    with open(checksum_file, "w", encoding="utf-8") as cf:
        json.dump(checksums, cf, indent=2)

    elapsed = round(time.time() - start_time, 2)
    print("============================================================")
    print(f" PIPELINE COMPLETED SUCCESSFULLY IN {elapsed} SECONDS")
    print(f" Checksums written to: {checksum_file}")
    print(f" Actual Output Counts:")
    print(f"   Products: {len(products):,}")
    print(f"   Locations: {len(locations):,}")
    print(f"   SKUs: {len(skus):,}")
    print(f"   Movements: {total_movements:,}")
    print(f"   Orders: {len(orders):,}")
    print(f"   Order Lines: {len(order_lines):,}")
    print(f"   Balances: {len(balances_list):,}")
    if anomaly_eval:
        print(f" Anomaly Detection Performance ({anomaly_eval.get('total_evaluated', 0)} evaluated):")
        print(f"   Precision: {anomaly_eval.get('precision', 0):.4f} | Recall: {anomaly_eval.get('recall', 0):.4f} | F1: {anomaly_eval.get('f1_score', 0):.4f}")
    print("============================================================")

    return {
        "status": "SUCCESS",
        "profile": profile,
        "seed": seed,
        "elapsed_seconds": elapsed,
        "records": {
            "products": len(products),
            "skus": len(skus),
            "locations": len(locations),
            "movements": total_movements,
            "orders": len(orders),
            "order_lines": len(order_lines),
            "balances": len(balances_list)
        },
        "checksums": checksums,
        "anomaly_evaluation": anomaly_eval,
        "validation_report": val_report
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="StockMind AI Synthetic Data Engine")
    parser.add_argument("--profile", type=str, default="starter", choices=["starter", "full"], help="Profile: starter or full")
    parser.add_argument("--seed", type=int, default=20261022, help="Deterministic random seed")
    parser.add_argument("--output", type=str, default="output", help="Output directory")
    parser.add_argument("--formats", type=str, default="csv,json,parquet", help="Comma-separated export formats")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch insertion size")
    parser.add_argument("--include-anomalies", action="store_true", default=True, help="Inject mandatory anomalies")
    parser.add_argument("--no-db", action="store_true", default=False, help="Skip database insertion")

    args = parser.parse_args()
    formats_list = [f.strip() for f in args.formats.split(",")]

    run_pipeline(
        profile=args.profile,
        seed=args.seed,
        output_dir=args.output,
        formats=formats_list,
        batch_size=args.batch_size,
        include_anomalies=args.include_anomalies,
        populate_db=not args.no_db
    )
