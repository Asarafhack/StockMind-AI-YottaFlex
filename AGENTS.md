# AGENTS.md — StockMind AI Architecture & Collaboration Guide

## Project Overview
**StockMind AI** is an enterprise-grade Unified Inventory Intelligence and Operations Platform built for the YottaFlex.ai Round 2 challenge.

**Core Tagline:** *Unified Inventory Intelligence. Every Unit Accounted For.*

## Primary Technology Stack
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (PostgreSQL + SQLite dynamic dialect fallback), Pydantic v2, Uvicorn
- **Data Engine:** NumPy, Faker, Polars, PyArrow, Pandas, Parquet
- **Frontend:** React 18/19, TypeScript, Vite, Tailwind CSS, Recharts, Lucide Icons, React Router DOM, TanStack Query
- **Testing:** Pytest, HTTPX, SQLite/PostgreSQL integration tests
- **Deployment & DevOps:** Docker, Docker Compose, GitHub Actions CI, Makefile

## Critical Engineering Invariants & Principles
1. **Ledger as Source of Truth:** `inventory_movements` is append-only. Never mutate or delete movement records. Adjustments and corrections require compensating movement entries.
2. **Deterministic Identifiers:**
   - Products: `PRD-000001`
   - SKUs: `SKU-000001`
   - Locations: `LOC-000001`
   - Orders: `ORD-2026-000001`
   - Order Lines: `ORDL-2026-000001-01`
   - Reservations: `RES-ORD-2026-000001-01`
   - Movements: `MOV-2026-00000001`
   - Shipments: `SHP-2026-000001`
   - Transfers: `TRN-2026-000001`
   - Replenishment Rules: `RPL-000001`
   - Anomalies: `ANOM-2026-000001`
3. **ATP Formula:**
   $$\text{ATP} = \text{ON\_HAND} - \text{ACTIVE\_RESERVATIONS} - \text{BLOCKED\_STOCK} + \text{ELIGIBLE\_INBOUND\_STOCK}$$
   Safety stock policy is strictly configurable to protect commitments without double deduction.
4. **Reservable Stock:**
   $$\text{RESERVABLE\_STOCK} = \text{ON\_HAND} - \text{BLOCKED\_STOCK} - \text{ACTIVE\_RESERVATIONS} - \text{SAFETY\_STOCK}$$
5. **No Double-Counting Transfers:** In-transit inventory exists exclusively in the transfer state between dispatch and receipt.
6. **No Blocked-Stock Fulfillment:** Damaged, blocked, or quarantined stock cannot be reserved or fulfilled.
7. **Ground Truth Separation:** Ground truth datasets (`ground_truth/`) are isolated from operational tables and detection features. No label leakage.
8. **Reproducibility:** Seed `20261022` produces byte-identical or deterministic checksum-verified datasets.

## Agent Responsibilities
- Keep `PROJECT_STATUS.md` updated after each milestone.
- Verify every feature with unit and integration tests before declaring completion.
- Never write placeholder buttons or mock data when real backend APIs exist.
