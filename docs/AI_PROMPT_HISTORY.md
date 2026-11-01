# StockMind AI — AI Prompt History Record

**Challenge:** YottaFlex.ai Associate AI Forward Deployed Engineer Round 2  
**Candidate Repository:** [https://github.com/Asarafhack/StockMind-AI-YottaFlex](https://github.com/Asarafhack/StockMind-AI-YottaFlex)  
**Disclosure Standard:** YottaFlex Recruitment FAQ Item 6 & Submission Guideline 03  
**Recording Date:** November 1, 2026  

---

## 1. Overview & Disclosure Notice

In full compliance with YottaFlex Candidate Project Guidelines ("03 USE LLMS TRANSPARENTLY: Submit your prompt history and explain where AI accelerated your work, where you relied heavily on it, and what you personally reviewed, changed, or validated"), this document contains the exact chronological record of all user-submitted prompts to AI coding assistants (Google Antigravity & Gemini) throughout the 72-hour development window.

No prompts have been redacted, falsified, or retrospectively manufactured. Per guideline requirements, AI model responses are omitted for conciseness; the full interactive execution transcripts and test logs are preserved on disk.

---

## 2. Chronological Prompt Log

### Prompt 1: Master Architecture & Core Build Specification
**Timestamp:** October 31, 2026  
**Tool:** Google Antigravity (Gemini 2.5 Pro Agentic Engine)  
**Role:** Principal Software Architect, Senior Python Engineer, Data Architect

```markdown
# MASTER BUILD PROMPT — STOCKMIND AI
## Enterprise Unified Inventory Intelligence & Operations Platform

### YOUR ROLE
Act as a principal software architect, senior Python engineer, senior full-stack developer, 
data engineer, database architect, QA automation engineer, DevOps engineer, and enterprise product designer.

You are responsible for designing, implementing, testing, documenting, and preparing a complete, 
production-quality software solution for the YottaFlex.ai Associate AI Forward Deployed Engineer Round 2 challenge.

Do not build a superficial demonstration, static dashboard, CRUD-only application, or UI-only prototype.
Build a complete, functional, testable, reproducible, scalable inventory management and intelligence platform.

Project name: STOCKMIND AI
Tagline: Unified Inventory Intelligence. Every Unit Accounted For.

Primary objective:
Unify inventory across physical stores, warehouses, and online channels while accurately accounting 
for reservations, blocked stock, safety stock, in-transit inventory, replenishment policies, order 
allocation, fulfillment, and inventory exceptions.

### NON-NEGOTIABLE REQUIREMENTS:
1. Implement every requirement in the original challenge.
2. Build functional frontend and backend.
3. Use a proper relational database and enforce foreign keys.
4. Implement all ten required core entities.
5. Generate realistic, deterministic synthetic data.
6. Support the full dataset target of:
   - 5,000 SKUs
   - 100 locations
   - 1,000,000 inventory movements
   - 50,000 orders
7. Implement all four required anomaly scenarios.
8. Maintain immutable movement history.
9. Implement accurate ATP calculations.
10. Implement reservation expiration and stock release.
11. Maintain complete order allocation and fulfillment traceability.
12. Export CSV, JSON, and SQL seed data.
13. Generate separate ground-truth labels.
14. Include comprehensive automated tests.
15. Demonstrate fixed-seed reproducibility using checksums.
16. Provide professional documentation and a working README.
17. Prepare a public GitHub repository.
18. Do not claim that an operation, test, deployment, or dataset generation succeeded unless it actually did.

### TECHNOLOGY STACK:
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.x, Pydantic v2, SQLite / PostgreSQL
- Data Engineering: Polars, PyArrow, NumPy, Faker
- Frontend: React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide React
- Testing: Pytest, HTTPX, SQLite in-memory integration fixtures
- Deployment: Docker, Docker Compose, GitHub Actions CI
```

---

### Prompt 2: Data Engine Pipeline Debugging & Schema Standardization
**Timestamp:** November 1, 2026 — 01:25 UTC  
**Tool:** Google Antigravity  
**Context:** During generation of the 1,000,000 movement full dataset, Polars failed on chunk concatenation with a compute error.

```markdown
Fix the StockMind AI full dataset generation failure.

Project:
C:\Users\asara\.gemini\antigravity\scratch\stockmind-ai

Actual error:
File: data_engine/run_pipeline.py
Line: 117
Code: df_movements = pl.DataFrame(all_movements)

Error:
polars.exceptions.ComputeError: could not append value: "LOC-000075" of type: str to the builder.

Requirements:
1. Inspect the actual movement generator and every field in its movement dictionaries.
2. Identify the exact column whose inferred type conflicts with the later string value.
3. Define an explicit, consistent Polars schema for all movement columns:
   - IDs must be strings.
   - Location IDs must be strings.
   - SKU IDs must be strings.
   - Movement types must be strings or their documented enum representation.
   - Timestamps must use a consistent datetime representation.
   - Quantities and monetary values must use appropriate numeric types.
4. Do not silently convert IDs into numbers or discard records.
5. Do not use a quick workaround that hides malformed records.
6. Prefer constructing typed DataFrames per batch and writing Parquet/CSV incrementally.
7. Preserve all 1,000,000 movements.
8. Preserve the fixed seed 20261022 and deterministic ordering.
9. Avoid retaining unnecessary copies of all million dictionaries in RAM.
10. Ensure database insertion and export operate correctly after the fix.
11. Ensure ground truth is generated separately from detection inputs.
12. Recompute SHA-256 checksums after successful exports.

Then run:
py -m data_engine.run_pipeline --profile starter --seed 20261022
Then run:
py -m data_engine.run_pipeline --profile full --seed 20261022

Verify actual output counts:
- 5,000 SKUs
- 100 locations
- 1,000,000 movements
- 50,000 orders
```

---

### Prompt 3: Independent Technical Verification & Audit Correction
**Timestamp:** November 1, 2026 — 09:15 UTC  
**Tool:** Google Antigravity  
**Context:** Independent inspection of the generated archive revealed three critical inconsistencies between the evaluation claims and the exported SQL/DB files.

```markdown
STOCKMIND AI — FINAL SUBMISSION CORRECTION & REPRODUCIBILITY AUDIT

The uploaded submission ZIP has been independently inspected. Do not rebuild the project from scratch. 
Fix the existing implementation while preserving the full dataset, deterministic seed (20261022), 
working frontend, and passing tests.

Critical issues found:
1. SQL export is incomplete:
   - seed.sql contained only products, locations, and 1,000 SKUs (truncated skus[:1000]).
   - Movements, balances, orders, order lines, and replenishment rules were omitted (0 records).
   - Generate full DDL and insert statements for all 16 tables without truncation.

2. Anomaly evaluation doesn't match the packaged database:
   - Operational tables (reservations, allocations, transfers, anomaly records) had 0 rows in sqlite file 
     due to SQLite WAL uncheckpointed pages.
   - Independent SQL reconciliation query returned 8 mismatches instead of the documented 4.
   - Fix Anomaly 3 so that blocked stock does not overwrite on_hand_quantity and create unintended drift.
   - Run explicit PRAGMA wal_checkpoint(TRUNCATE) before packaging.
   - Ensure evaluate_ground_truth matches on both entity_id and issue_type.

3. Documentation and evaluation report reconciliation:
   - README and PROJECT_STATUS.md documented 10 scenarios (4 TP, 6 TN).
   - Actual anomaly_evaluation.json reports 116 scenarios (16 TP, 100 TN).
   - Reconcile documentation to match actual reproducible numbers.
   - Differentiate 12.42s in-memory generator benchmark from full ~474s pipeline execution.
```

---

### Prompt 4: Final Comprehensive Project Audit & Submission Handover
**Timestamp:** November 1, 2026 — 17:00 UTC  
**Tool:** Google Antigravity  
**Context:** Final comprehensive review to ensure submission perfection across code, QA, security, documentation, and Git repository state.

```markdown
# FINAL PROJECT AUDIT & SUBMISSION READINESS — STOCKMIND AI | YOTTAFLEX ROUND 2

Act as a Senior AI Engineer, Forward Deployed Engineer, Data Architect, QA Engineer and Technical Documentation Specialist.
Your task is to perform a comprehensive audit and final improvement of my EXISTING project:
Project: StockMind AI – YottaFlex Round 2
GitHub repository: https://github.com/Asarafhack/StockMind-AI-YottaFlex
Local project directory: C:\Users\asara\.gemini\antigravity\scratch\stockmind-ai

IMPORTANT: Do not rebuild the project from scratch. First inspect every existing component, 
understand the architecture, identify actual gaps and improve the existing implementation.

Requirements:
- Phase 1: Complete Project Audit
- Phase 2: Verify All Business Requirements (10 entities, deterministic IDs, ATP, reservations, transfers, ledger)
- Phase 3: Synthetic Data and Reproducibility (5k SKUs, 100 locs, 1M movements, 50k orders, seed 20261022)
- Phase 4: Validation and Testing (automated validations, 18 passing tests, normal/boundary/negative cases)
- Phase 5: Frontend and Backend Quality (React 18 + TS + Vite, 10 pages, dark navy enterprise UI)
- Phase 6: Professional Documentation (README.md, DATA_DICTIONARY.md, ARCHITECTURE.md, VALIDATION_REPORT.md, 
  AI_DISCLOSURE.md, AI_PROMPT_HISTORY.md, KNOWN_LIMITATIONS.md)
- Phase 7: Security and Repository Cleanup (.gitignore, no secrets, untrack large binaries > 50MB)
- Phase 8: Final Acceptance Report (FINAL_ACCEPTANCE_REPORT.md with PASS/FAIL matrix)
- Phase 9: Final Execution and Handover (exact git commands, test proof)
```
