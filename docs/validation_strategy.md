# StockMind AI — Enterprise Data Validation Strategy

## 1. Overview
The Data Validation Engine (`data_engine/validators/data_validator.py`) runs automated integrity audits across the relational database. It ensures that every record conforms to structural, arithmetic, relational, and business lifecycle constraints.

---

## 2. Validation Rule Categories

### 2.1 Primary Key & Uniqueness
- `PK-001-SKU-CODE-UNIQUE`: Checks that every SKU code is globally unique across the catalog.
- `PK-002-LOCATION-CODE-UNIQUE`: Checks that facility identifiers are unique.
- `UQ-001-BALANCE-SKU-LOCATION`: Verifies that only one balance projection exists per SKU-location combination.

### 2.2 Foreign Key Integrity
- `FK-001-SKU-PRODUCT`: All SKUs must resolve to an existing row in `products`.
- `FK-002-BALANCE-SKU`: All balances must resolve to an existing `skus` record.
- `FK-003-MOVEMENT-SKU-LOC`: All movements must reference valid SKUs and existing source/destination nodes.
- `FK-004-ORDERLINE-ORDER`: Order lines must reference valid parent orders.
- `FK-005-RESERVATION-ORDERLINE`: Reservations must resolve to active order lines.

### 2.3 Enum & Status Constraints
- `ENUM-001-LOCATION-TYPE`: Validates against allowed location types (`Warehouse`, `Distribution Center`, `Retail Store`, `Fulfillment Center`, `Online Channel`).
- `ENUM-002-ORDER-CHANNEL`: Validates channels (`ONLINE`, `RETAIL`, `MARKETPLACE`, `B2B`).
- `ENUM-003-MOVEMENT-TYPE`: Enforces standardized movement taxonomy.

### 2.4 Chronology & Date Constraints
- `DATE-001-TRANSFER-CHRONOLOGY`: Checks that `dispatched_at <= received_at`.
- `DATE-002-RESERVATION-EXPIRY`: Verifies that `expires_at > reserved_at`.
- `DATE-003-SHIPMENT-DELIVERY`: Verifies that `shipped_at <= delivered_at`.

### 2.5 Arithmetic & Balance Integrity
- `ARITH-001-NEGATIVE-ON-HAND`: Verifies that physical on-hand stock never drops below zero.
- `ARITH-002-RECONCILIATION-BALANCE`: Validates that derived balances match the cumulative sum of movements.
- `ARITH-003-RESERVATION-SUM`: Verifies that `reserved_quantity` matches the sum of active reservation records.

### 2.6 Lifecycle State Transitions
- `LIFE-001-STALE-ACTIVE-RESERVATION`: Flags reservations marked `ACTIVE` whose TTL timestamp has elapsed.
- `LIFE-002-FULFILLMENT-STATUS`: Flags orders marked `SHIPPED` without associated shipments or sale movements.
