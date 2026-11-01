# StockMind AI — Automated Validation & Quality Assurance Report

**Challenge:** YottaFlex.ai Associate AI Forward Deployed Engineer Round 2  
**Dataset Scale:** Full Scale Profile (5,000 SKUs, 100 Locations, 1,000,000 Movements, 50,000 Orders)  
**Fixed Seed:** `20261022`  
**Overall Quality Status:** **ALL VALIDATIONS PASSED (100% GREEN)**  
**Report Date:** November 1, 2026  

---

## 1. Executive Summary

StockMind AI includes a comprehensive, multi-layer validation engine that verifies database relational integrity, inventory business logic invariants, temporal ordering, and arithmetic correctness.

- **Automated Relational Rules:** **25 / 25 PASSED** (0 failures)
- **Pytest Automated Test Suite:** **18 / 18 PASSED** in 5.49 seconds
- **Enterprise Anomaly Detection:** **116 / 116 Scenarios Verified** (Precision: 1.0000, Recall: 1.0000, F1: 1.0000)
- **Seed Checksum Verification:** **27 / 27 Files Matched**

---

## 2. Automated Relational Validation Suite (25 Rules)

The automated validator (`data_engine/validators/data_validator.py`) inspects the operational SQLite database across six validation categories:

| Rule ID | Category | Validated Invariant | Records Inspected | Result |
|---|---|---|:---:|:---:|
| `PK-001-PRD` | Primary Key | `products.product_id` uniqueness and non-null | 2,000 | **PASS** |
| `PK-002-SKU` | Primary Key | `skus.sku_id` uniqueness and non-null | 5,000 | **PASS** |
| `PK-003-LOC` | Primary Key | `locations.location_id` uniqueness and non-null | 100 | **PASS** |
| `PK-004-BAL` | Primary Key | `inventory_balances.balance_id` uniqueness | 500,000 | **PASS** |
| `PK-005-MOV` | Primary Key | `inventory_movements.movement_id` uniqueness | 1,000,000 | **PASS** |
| `PK-006-ORD` | Primary Key | `orders.order_id` uniqueness | 50,000 | **PASS** |
| `PK-007-LINE` | Primary Key | `order_lines.order_line_id` uniqueness | 85,289 | **PASS** |
| `FK-001-SKU-PRD` | Foreign Key | Every SKU links to a valid existing Product | 5,000 | **PASS** |
| `FK-002-BAL-SKU` | Foreign Key | Every balance links to a valid existing SKU | 500,000 | **PASS** |
| `FK-003-BAL-LOC` | Foreign Key | Every balance links to a valid existing Location | 500,000 | **PASS** |
| `FK-004-MOV-SKU` | Foreign Key | Every movement references a valid existing SKU | 1,000,000 | **PASS** |
| `FK-005-ORDL-ORD` | Foreign Key | Every order line references a valid existing Order | 85,289 | **PASS** |
| `FK-006-ORDL-SKU` | Foreign Key | Every order line references a valid existing SKU | 85,289 | **PASS** |
| `FK-007-ALC-LINE` | Foreign Key | Every allocation references a valid Order Line | 4 | **PASS** |
| `ENUM-001-LOC-TYPE` | Enum Domain | `location_type` in allowed facility taxonomy | 100 | **PASS** |
| `ENUM-002-MOV-TYPE` | Enum Domain | `movement_type` in allowed ledger movement types | 1,000,000 | **PASS** |
| `ENUM-003-ORD-STAT` | Enum Domain | `order_status` in allowed lifecycle states | 50,000 | **PASS** |
| `ENUM-004-CHANNEL` | Enum Domain | `channel` in allowed omnichannel identifiers | 50,000 | **PASS** |
| `DATE-001-MOV-OCC` | Date Ordering | `movement.recorded_at >= movement.occurred_at` | 1,000,000 | **PASS** |
| `DATE-002-TRN-TIME` | Date Ordering | `transfer.received_at >= transfer.dispatched_at` (excluding intentional anomaly) | 4 | **PASS** |
| `DATE-003-RES-EXP` | Date Ordering | `reservation.expires_at > reservation.reserved_at` | 4 | **PASS** |
| `ARITH-001-ON-HAND` | Arithmetic | `inventory_balances.on_hand_quantity >= 0` across all records | 500,000 | **PASS** |
| `ARITH-002-TOTAL-AMT` | Arithmetic | Order `total_amount >= 0` | 50,000 | **PASS** |
| `LIFE-001-RES-STALE` | Lifecycle | No unexpired reservations flagged as `EXPIRED` | 4 | **PASS** |
| `LIFE-002-TRN-STAT` | Lifecycle | In-transit transfer status matches shipment tracking | 4 | **PASS** |

---

## 3. Automated Pytest Test Suite Results (18 Tests)

Command: `pytest -v backend/tests`  
Execution Time: **5.49 seconds**  
Result: **18 passed, 0 failed, 0 errors**

| Test Module | Test Name | Invariant Under Test | Status | Duration |
|---|---|---|:---:|:---:|
| `test_anomalies.py` | `test_four_mandatory_anomalies_detected` | All 4 enterprise anomaly classes detected simultaneously | **PASSED** | 0.28s |
| `test_api.py` | `test_api_products_crud` | REST CRUD operations for Products | **PASSED** | 0.32s |
| `test_api.py` | `test_api_skus_crud` | REST CRUD operations for SKUs | **PASSED** | 0.29s |
| `test_api.py` | `test_api_locations_crud` | REST CRUD operations for Locations | **PASSED** | 0.31s |
| `test_api.py` | `test_api_inventory_and_atp` | Real-time balance and ATP computation endpoints | **PASSED** | 0.30s |
| `test_api.py` | `test_api_analytics_overview_and_what_if` | Executive KPIs, category accuracy, and What-If simulator | **PASSED** | 0.34s |
| `test_atp.py` | `test_atp_standard_formula` | Standard formula: $OH - R - B + I_e$ | **PASSED** | 0.31s |
| `test_atp.py` | `test_atp_with_eligible_inbound_transfer` | Inclusion of confirmed `IN_TRANSIT` transfers | **PASSED** | 0.33s |
| `test_atp.py` | `test_atp_policy_strict_on_hand_only` | Exclusion of inbound transfers under strict policy | **PASSED** | 0.29s |
| `test_atp.py` | `test_atp_zero_clamping_boundary` | Negative reservation/blocked conditions clamped to 0 | **PASSED** | 0.28s |
| `test_atp.py` | `test_atp_excludes_expired_reservations` | Stale reservations automatically excluded from deductions | **PASSED** | 0.30s |
| `test_orders.py` | `test_order_allocation_and_fulfillment` | Allocation, movement debit, and shipment generation | **PASSED** | 0.35s |
| `test_orders.py` | `test_order_backorder_when_insufficient_stock` | Partial allocation and backorder transitions under zero stock | **PASSED** | 0.32s |
| `test_reproducibility.py` | `test_fixed_seed_reproducibility` | Seed `20261022` yields identical record distributions | **PASSED** | 0.26s |
| `test_reproducibility.py` | `test_different_seeds_produce_different_distributions` | Seed variation produces statistically distinct datasets | **PASSED** | 0.25s |
| `test_reservations.py` | `test_reservation_lifecycle_and_expiry` | Active holds, TTL expiry sweep, and stock restoration | **PASSED** | 0.31s |
| `test_reservations.py` | `test_negative_oversell_rejection` | Rejection of reservation requests exceeding stock | **PASSED** | 0.28s |
| `test_transfers.py` | `test_transfer_lifecycle_and_zero_double_counting` | Two-phase dispatch and receipt without double counting | **PASSED** | 0.32s |

---

## 4. Anomaly Detection Performance Evaluation (116 Scenarios)

The anomaly detection engine was evaluated against 116 labeled test scenarios (16 injected true positives and 100 benign control scenarios) operating strictly against operational database records:

| Anomaly Class | Evaluation Target | Detected TPs | False Positives | False Negatives | Precision | Recall | F1 Score |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1. Balance Mismatch** | 4 Injected | 4 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| **2. Reservation Overflow** | 4 Injected | 4 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| **3. Blocked Stock Fulfillment** | 4 Injected | 4 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| **4. Premature Transfer** | 4 Injected | 4 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| **Benign Controls** | 100 Controls | 100 (TNs) | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| **TOTAL SUMMARY** | **116 Scenarios** | **16 TP / 100 TN** | **0** | **0** | **1.0000** | **1.0000** | **1.0000** |

---

## 5. Independent SQL Ledger Reconciliation Proof

Executing the SQL ledger balance reconciliation query directly against the 1,000,000-movement database:

```sql
SELECT 
    b.sku_id,
    b.location_id,
    b.on_hand_quantity,
    (COALESCE(inbound.qty, 0) - COALESCE(outbound.qty, 0)) AS ledger_on_hand
FROM inventory_balances b
LEFT JOIN (
    SELECT sku_id, destination_location_id, SUM(quantity) AS qty
    FROM inventory_movements
    WHERE movement_type IN ('OPENING_BALANCE', 'RECEIPT', 'CUSTOMER_RETURN', 'TRANSFER_RECEIPT', 'ADJUSTMENT_IN')
    GROUP BY sku_id, destination_location_id
) inbound ON b.sku_id = inbound.sku_id AND b.location_id = inbound.destination_location_id
LEFT JOIN (
    SELECT sku_id, source_location_id, SUM(quantity) AS qty
    FROM inventory_movements
    WHERE movement_type IN ('SALE', 'TRANSFER_DISPATCH', 'ADJUSTMENT_OUT', 'DAMAGE')
    GROUP BY sku_id, source_location_id
) outbound ON b.sku_id = outbound.sku_id AND b.location_id = outbound.source_location_id
WHERE b.on_hand_quantity != (COALESCE(inbound.qty, 0) - COALESCE(outbound.qty, 0));
```

**Actual Execution Result:**
```
Actual Balance Mismatches in Database: 4
  1. SKU-000001 / LOC-000001: Balance 675 vs Ledger 600 (Drift: +75 units) [INJECTED ANOMALY]
  2. SKU-000002 / LOC-000002: Balance 405 vs Ledger 305 (Drift: +100 units) [INJECTED ANOMALY]
  3. SKU-000003 / LOC-000003: Balance 372 vs Ledger 247 (Drift: +125 units) [INJECTED ANOMALY]
  4. SKU-000004 / LOC-000004: Balance 768 vs Ledger 618 (Drift: +150 units) [INJECTED ANOMALY]
```
Zero accidental balance mismatches exist across the remaining 499,996 balance records.
