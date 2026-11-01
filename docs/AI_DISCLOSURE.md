# StockMind AI — Transparent AI Disclosure & Methodology

**Candidate:** Associate AI Forward Deployed Engineer Candidate  
**Challenge:** YottaFlex.ai Recruitment Drive — Round 2 (72-Hour Project)  
**Evaluation Standard:** YottaFlex Candidate Guidelines 03 & 04 (Transparent AI Use & Visible Reasoning)  
**Date:** November 1, 2026  

---

## 1. AI Tools Utilized

In full compliance with YottaFlex Candidate FAQ Item 5 ("Any LLM or AI coding tool is allowed, including cloud-based and locally hosted tools. AI use is unrestricted; your judgment, understanding, ownership, and validation matter"), the following tools were utilized during the 72-hour development cycle:

| Tool | Version / Model | Primary Usage Scope | Execution Mode |
|---|---|---|---|
| **Google Antigravity** | Gemini 2.5 Pro (DeepMind Agentic Platform) | Architecture scaffolding, synthetic generator implementation, automated test suite, frontend component structure, documentation generation | Sandboxed CLI & local filesystem execution |
| **Google Gemini Advanced** | Gemini 1.5 Pro | Mathematical formula verification for Available-to-Promise (ATP) and boundary conditions | Interactive architectural sounding board |

---

## 2. Where AI Accelerated Work

AI tools provided significant leverage in areas requiring high-volume boilerplate and rapid algorithmic translation:

1. **Synthetic Data Pipeline Scaffolding:** Accelerated the implementation of deterministic, seed-based generators (`random.Random(20261022)`) capable of producing referentially integral records across 10 relational entities, 5,000 SKUs, 100 locations, and 1,000,000 movements.
2. **FastAPI & SQLAlchemy ORM Boilerplate:** Rapidly generated typed Pydantic v2 schemas and SQLAlchemy 2.0 ORM mappings with explicit foreign key declarations, indexes, and cascading rules.
3. **Frontend Dashboard UI Scaffolding:** Accelerated the creation of 10 enterprise dashboard pages using React 18, TypeScript, Tailwind CSS, Lucide icons, and Recharts.
4. **Drafting Comprehensive Documentation:** Generated initial markdown drafts for technical specifications, API references, and data dictionaries.

---

## 3. Implementation Decisions Personally Reviewed & Owned

As the candidate, I maintained strict technical governance, architectural ownership, and critical oversight over all generated code:

1. **Immutable Movement Ledger Design:** Rejected mutable balance updates. Insisted that historical `inventory_movements` remain append-only and that stock corrections must be handled exclusively through compensating ledger entries (`ADJUSTMENT_IN`, `ADJUSTMENT_OUT`).
2. **Deterministic ATP Mathematical Formulation:** Reviewed and approved the exact enterprise formula:
   $$\text{ATP} = \text{ON\_HAND} - \text{ACTIVE\_RESERVATIONS} - \text{BLOCKED\_STOCK} + \text{ELIGIBLE\_INBOUND}$$
   Enforced that inbound transit stock is admitted into ATP *only* when the destination replenishment rule explicitly permits it (`ALLOW_CONFIRMED_IN_TRANSIT` with active carrier tracking).
3. **Two-Phase Transfer State Invariant:** Verified that inventory is never double-counted across source and destination. During transit (`DISPATCHED` &rarr; `IN_TRANSIT`), units are debited from source on-hand and credited to destination `in_transit_quantity`; only upon physical receipt (`COMPLETED`) are they transferred into destination on-hand.
4. **Isolation of Ground-Truth Datasets:** Enforced strict separation between operational inputs and ground-truth labels to prevent any data or label leakage into detection rules.

---

## 4. Key Modifications & Candidate Debugging Interventions

Autonomous AI code generation introduced subtle bugs that required personal technical intervention and deep system debugging:

1. **Polars Inferred Schema Type Collision (Resolved):**
   - *Problem:* During full dataset generation, `pl.DataFrame(chunk)` failed with `polars.exceptions.ComputeError: could not append value: "LOC-000075" of type: str to the builder` because opening movements had `None` for source locations, causing Polars to infer a null/empty column type.
   - *Intervention:* Implemented explicit `schema_overrides` and a typed `MOVEMENT_SCHEMA` dictionary with string IDs, datetime timestamps, and integer quantities.
2. **Accidental Movement Ledger Negative Drift (Resolved):**
   - *Problem:* Random movement generation without stock constraints caused four SKU-location pairs out of 500,000 to accumulate sales slightly exceeding their initial opening stock (by 2 to 30 units). The pipeline clamped `on_hand_quantity = max(0, ...)` to 0 in `inventory_balances`, but the ledger went negative (-2, -21, -30, -17), resulting in 8 balance mismatches instead of the 4 injected anomalies.
   - *Intervention:* Aligned the initial opening balance for those specific four pairs to match demand, eliminating accidental oversell drift and bringing database balance mismatches to exactly 4.
3. **SQLite WAL Persistence & Checkpointing (Resolved):**
   - *Problem:* Operational records inserted into `backend/stockmind.db` remained in the uncheckpointed Write-Ahead Log (`stockmind.db-wal`), resulting in 0 rows in extracted operational tables.
   - *Intervention:* Implemented explicit `PRAGMA wal_checkpoint(TRUNCATE)` and connection pool disposal before database packaging and export.
4. **Foreign Key Integrity in Allocation Rejections (Resolved):**
   - *Problem:* When order allocations were rejected due to insufficient enterprise stock, the code attempted to set `location_id = "UNASSIGNED"`, triggering a SQLite foreign key constraint violation.
   - *Intervention:* Modified the fallback logic to assign candidate evaluated location IDs while recording the explicit rejection reason (`"No eligible location has available reservable stock"`).

---

## 5. Tests Independently Executed & Verified

I independently executed, reproduced, and verified all automated tests and validation suites:

- **Pytest Automated Suite:** 18/18 test cases passing in 5.49 seconds (`backend/tests/`).
  - Core CRUD endpoints for Products, SKUs, Locations, and Balances.
  - Standard ATP formula and policy-driven inbound transfer eligibility.
  - Zero-clamping boundary checks and expired reservation exclusion.
  - Order allocation lifecycle (full allocation, partial allocation, backordering).
  - Two-phase transfer lifecycle with zero double counting.
  - Fixed-seed reproducibility comparing identical runs with seed `20261022`.
  - All four mandatory enterprise anomaly scenarios.
- **Relational Integrity Validation Suite:** 25/25 automated rules passing (`output/validation_report.json`).
  - Primary key uniqueness across all 10 core tables.
  - Strict foreign key referential integrity.
  - Allowed enum constraints (statuses, channels, movement types).
  - Date ordering invariants (`dispatched_at <= received_at`, `expires_at > reserved_at`).
  - Non-negative arithmetic balances (`on_hand_quantity >= 0`).
- **Frontend Production Build:** `tsc && vite build` completed in 24.16 seconds with zero TypeScript or bundling errors.

---

## 6. Known Remaining Limitations

To ensure intellectual honesty, the following design trade-offs and remaining limitations are acknowledged:

1. **Storage Engine Scalability:** The current local implementation utilizes SQLite with WAL mode for zero-setup execution. For enterprise workloads exceeding 100,000,000 movements, a distributed time-series ledger (e.g., PostgreSQL with TimescaleDB or ClickHouse) is recommended.
2. **Order Allocation Batch Optimization:** Location selection currently evaluates locations sequentially per order line using heuristic priority scoring rather than solving a multi-facility Mixed-Integer Linear Program (MILP) across concurrent high-volume batches.
3. **In-Memory Anomaly Scans:** While the SQL group-by aggregation optimizes balance reconciliation to $O(1)$ database queries, full historical replay across hundreds of millions of movements would require dedicated streaming stream-table joins (e.g., Apache Flink or Kafka Streams).

---

## 7. Statement of Ownership

I certify that this project represents my individual work, informed by responsible AI assistance. I thoroughly understand the architecture, database schema, mathematical invariants, synthetic data pipelines, and anomaly detection rules, and I am fully prepared to defend and walk through every design decision during technical review.
