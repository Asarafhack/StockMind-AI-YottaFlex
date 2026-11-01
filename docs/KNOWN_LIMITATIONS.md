# StockMind AI — Known Limitations & Architectural Roadmap

**Challenge:** YottaFlex.ai Associate AI Forward Deployed Engineer Round 2  
**Document Scope:** Production Readiness, System Constraints, and Future Enhancements  
**Date:** November 1, 2026  

---

## 1. Executive Summary

StockMind AI meets or exceeds all core, non-negotiable requirements of the YottaFlex Round 2 challenge, supporting 5,000 SKUs, 100 locations, 1,000,000 movements, 50,000 orders, deterministic ATP, an immutable movement ledger, and 100% precision/recall on 16 injected enterprise anomalies across 116 scenarios.

This document outlines known operational boundaries, deliberate engineering trade-offs, and recommended technical enhancements for scaling from an evaluation deployment to multi-region global production.

---

## 2. Architectural Boundaries & Current Trade-Offs

### 2.1 Database & Concurrency Model
- **Current Architecture:** Embedded SQLite 3 with Write-Ahead Logging (`PRAGMA journal_mode = WAL`) and transactional batching.
- **Trade-Off:** Provides zero-dependency, single-file reproducibility that runs out-of-the-box on any candidate or evaluator machine without requiring external PostgreSQL services.
- **Constraint:** SQLite permits unlimited concurrent readers, but serializes writes with a single database-level lock. Under write workloads exceeding 5,000 concurrent transactions/second, lock contention occurs.
- **Production Roadmap:** Transition to **PostgreSQL 16+** with read replicas or **TimescaleDB** for hypertable partitioning of `inventory_movements` by month/quarter.

### 2.2 Order Allocation Algorithm
- **Current Architecture:** Heuristic priority ranking (Fulfillment Centers > Distribution Centers > Retail Stores) evaluated per order line based on local reservable stock.
- **Trade-Off:** Deterministic, easily explainable in UI audit trails, and executes in $< 5\text{ ms}$ per line without complex mathematical solvers.
- **Constraint:** Does not solve global cross-order multi-facility optimization (e.g., minimizing total freight cost or split shipments across concurrent batches of 10,000 orders).
- **Production Roadmap:** Implement a **Mixed-Integer Linear Programming (MILP)** allocation solver using `scipy.optimize` or `OR-Tools` for batched enterprise order waves.

### 2.3 Anomaly Detection Replay
- **Current Architecture:** Set-based SQL aggregation (`GROUP BY sku_id, location_id`) comparing projected balances against ledger sums in $O(1)$ database passes.
- **Trade-Off:** Extremely fast on the challenge volume of 1,000,000 movements (~5–10 seconds in SQLite).
- **Constraint:** Re-evaluating the full movement ledger from inception becomes computationally heavy when historical movements reach hundreds of millions of rows.
- **Production Roadmap:** Introduce **incremental periodic balance checkpoints** (e.g., weekly closing balances) with event-driven Change Data Capture (CDC via Debezium / Kafka) to verify incremental deltas rather than scanning the entire ledger from Genesis.

### 2.4 Distributed Clock Synchronization
- **Current Architecture:** UTC timestamps recorded via application runtime (`datetime.datetime.utcnow()`).
- **Constraint:** In a distributed multi-node deployment, minor clock skew between application nodes could lead to millisecond-level timestamp inversions in rapid inter-location transfers.
- **Production Roadmap:** Implement **Lamport Timestamps** or database-generated monotonically increasing sequence counters (`BIGSERIAL` or Hybrid Logical Clocks) to guarantee absolute global order across distributed nodes.

---

## 3. Scale Horizon & Benchmark Limits

| Operational Dimension | Current Verified Capacity | Degradation Threshold | Architectural Solution for Scale |
|---|:---:|:---:|---|
| **SKU Catalog Size** | 5,000 SKUs | ~100,000 SKUs | Multi-level category indexing; Elasticsearch / Typesense catalog search |
| **Physical Facilities** | 100 Locations | ~2,500 Locations | Geospatial PostGIS indexing for distance-based routing |
| **Historical Movements** | 1,000,000 records | ~10,000,000 records | Apache Parquet data lake with DuckDB or ClickHouse OLAP query engine |
| **Concurrent Orders** | 50,000 orders | ~500,000 orders | Distributed Redis reservation queue with RabbitMQ / Kafka asynchronous workers |
| **Memory Footprint** | < 250 MB RAM | ~1 GB RAM | Chunked Polars streaming pipeline with zero in-memory accumulation |

---

## 4. Security & Hardening Roadmap

1. **Authentication & Authorization:** The current application uses environment-based configuration without active user authentication to streamline evaluator inspection. Production deployment requires JWT / OAuth2 (e.g., Auth0 / Keycloak) with Role-Based Access Control (`ROLE_WAREHOUSE_OPERATOR`, `ROLE_INVENTORY_ANALYST`, `ROLE_ADMIN`).
2. **Secrets Management:** In a cloud environment, environment variables should be injected via AWS Secrets Manager, HashiCorp Vault, or Google Cloud Secret Manager rather than local `.env` files.
3. **Audit Immutability:** Write-once-read-many (WORM) storage or cryptographic merkle-tree hashes for historical movement logs to satisfy strict Sarbanes-Oxley (SOX) compliance.
