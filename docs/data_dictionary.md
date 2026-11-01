# StockMind AI — Relational Data Dictionary

This document details the ten core relational entities and bridge tables, their database constraints, field definitions, and lifecycle states.

---

## 1. Product (`products`)
Represents the catalog merchandise product group.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `product_id` | VARCHAR(32) | NO | PK | Deterministic identifier (e.g. `PRD-000001`) |
| `product_name` | VARCHAR(255) | NO | INDEX | Brand product display title |
| `description` | TEXT | YES | - | Full markdown/text merchandise description |
| `brand` | VARCHAR(128) | NO | INDEX | Manufacturer / Brand identity |
| `category` | VARCHAR(128) | NO | INDEX | Top-level merchandise category |
| `product_status`| VARCHAR(32) | NO | - | Status (`ACTIVE`, `INACTIVE`, `DISCONTINUED`) |
| `created_at` | TIMESTAMP | NO | - | Creation timestamp |
| `updated_at` | TIMESTAMP | NO | - | Last modification timestamp |

---

## 2. SKU (`skus`)
Stock Keeping Unit variant specifying physical properties and pricing.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `sku_id` | VARCHAR(32) | NO | PK | Deterministic identifier (e.g. `SKU-000001`) |
| `product_id` | VARCHAR(32) | NO | FK (`products.product_id`) | Foreign key to parent product |
| `sku_code` | VARCHAR(64) | NO | UNIQUE, INDEX | Scannable internal SKU code |
| `barcode` | VARCHAR(64) | YES | UNIQUE, INDEX | Scannable EAN/UPC barcode |
| `variant` | VARCHAR(128) | NO | - | Color, size, or material descriptor |
| `unit_of_measure` | VARCHAR(32)| NO | - | Base unit (`EACH`, `BOX`, `PALLET`) |
| `unit_cost` | NUMERIC(12,2)| NO | - | Direct procurement unit cost (USD) |
| `selling_price`| NUMERIC(12,2)| NO | - | Commercial selling price (USD) |
| `weight` | FLOAT | YES | - | Unit shipping weight in kilograms |
| `status` | VARCHAR(32) | NO | - | Status (`ACTIVE`, `DISCONTINUED`) |
| `created_at` | TIMESTAMP | NO | - | Creation timestamp |

---

## 3. Location (`locations`)
Physical facilities and digital sales channels.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `location_id` | VARCHAR(32) | NO | PK | Deterministic identifier (e.g. `LOC-000001`) |
| `location_code`| VARCHAR(64) | NO | UNIQUE, INDEX | Alphanumeric node identifier |
| `location_name`| VARCHAR(255) | NO | - | Facility display name |
| `location_type`| VARCHAR(64) | NO | INDEX | Type: `Warehouse`, `Distribution Center`, `Retail Store`, `Fulfillment Center`, `Online Channel` |
| `parent_location_id` | VARCHAR(32) | YES | FK (`locations.location_id`) | Optional self-reference for node hierarchy |
| `address` | VARCHAR(255) | NO | - | Street address |
| `city` | VARCHAR(128) | NO | INDEX | Municipality |
| `region` | VARCHAR(128) | NO | - | State / Province |
| `country` | VARCHAR(64) | NO | - | Country code (`USA`) |
| `timezone` | VARCHAR(64) | NO | - | IANA timezone string |
| `active_status`| BOOLEAN | NO | - | Operational flag |
| `created_at` | TIMESTAMP | NO | - | Creation timestamp |

---

## 4. InventoryBalance (`inventory_balances`)
Derived balance projection materialized for operational performance.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `balance_id` | VARCHAR(32) | NO | PK | Deterministic identifier (e.g. `BAL-000001`) |
| `sku_id` | VARCHAR(32) | NO | FK (`skus.sku_id`) | SKU reference |
| `location_id` | VARCHAR(32) | NO | FK (`locations.location_id`) | Location reference |
| `on_hand_quantity` | INTEGER | NO | - | Total physical stock currently present |
| `reserved_quantity`| INTEGER | NO | - | Units committed to active orders |
| `blocked_quantity` | INTEGER | NO | - | Damaged, quarantined, or recalled stock |
| `safety_stock_quantity` | INTEGER | NO | - | Protected buffer threshold |
| `in_transit_quantity` | INTEGER | NO | - | Dispatched inbound stock in transit |
| `available_quantity` | INTEGER | NO | - | Free unallocated physical stock: $OH - R - B$ |
| `last_movement_id` | VARCHAR(32) | YES | - | Most recent movement updating this record |
| `version` | INTEGER | NO | - | Concurrency lock version counter |
| `updated_at` | TIMESTAMP | NO | - | Timestamp of latest balance update |

*Constraint:* `UNIQUE(sku_id, location_id)` enforced across all database dialects.

---

## 5. InventoryMovement (`inventory_movements`)
Immutable, append-only operational ledger. The authoritative single source of truth.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `movement_id` | VARCHAR(32) | NO | PK | Deterministic identifier (e.g. `MOV-2026-00000001`) |
| `sku_id` | VARCHAR(32) | NO | FK (`skus.sku_id`) | Affected item |
| `source_location_id` | VARCHAR(32) | YES | FK (`locations.location_id`) | Debited origin facility |
| `destination_location_id` | VARCHAR(32) | YES | FK (`locations.location_id`) | Credited destination facility |
| `movement_type`| VARCHAR(64) | NO | INDEX | Event type (see Section 5.1) |
| `quantity` | INTEGER | NO | - | Non-negative integer magnitude |
| `reference_type`| VARCHAR(64) | NO | - | Business event category (`ORDER`, `TRANSFER`, etc.) |
| `reference_id` | VARCHAR(64) | YES | INDEX | Foreign document identifier |
| `transfer_id` | VARCHAR(32) | YES | INDEX | Inter-facility transfer reference |
| `occurred_at` | TIMESTAMP | NO | INDEX | Physical event execution timestamp |
| `recorded_at` | TIMESTAMP | NO | - | System ingestion timestamp |
| `reason_code` | VARCHAR(64) | YES | - | Standard operational reason code |
| `created_by` | VARCHAR(64) | NO | - | System engine or user identity |
| `metadata_json`| TEXT | YES | - | Contextual payload |

### 5.1 Allowed Movement Types
- `OPENING_BALANCE` (Initial facility stocking)
- `RECEIPT` (PO inbound from supplier)
- `SALE` (Order fulfillment consumption)
- `CUSTOMER_RETURN` (Merchandise return accepted)
- `TRANSFER_DISPATCH` (Outbound transit from facility)
- `TRANSFER_RECEIPT` (Inbound transit check-in at destination)
- `ADJUSTMENT_IN` (Positive cycle-count correction)
- `ADJUSTMENT_OUT` (Negative cycle-count correction)
- `DAMAGE` (Quarantine write-down)
- `BLOCK` (Quality assurance lot hold)
- `UNBLOCK` (Quality assurance lot release)

---

## 6. Reservation (`reservations`)
Temporary atomic allocation hold tied to customer order line.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `reservation_id` | VARCHAR(64) | NO | PK | Deterministic identifier (`RES-ORD-...`) |
| `order_id` | VARCHAR(32) | NO | FK (`orders.order_id`) | Associated customer order |
| `order_line_id` | VARCHAR(32) | NO | FK (`order_lines.order_line_id`) | Associated line item |
| `sku_id` | VARCHAR(32) | NO | FK (`skus.sku_id`) | Reserved SKU |
| `location_id` | VARCHAR(32) | NO | FK (`locations.location_id`) | Committed facility node |
| `quantity` | INTEGER | NO | - | Reserved unit count |
| `reservation_status` | VARCHAR(32) | NO | INDEX | `ACTIVE`, `EXPIRED`, `RELEASED`, `FULFILLED`, `CANCELLED` |
| `reserved_at` | TIMESTAMP | NO | - | Lock reservation creation time |
| `expires_at` | TIMESTAMP | NO | INDEX | TTL expiration timestamp |
| `released_at` | TIMESTAMP | YES | - | Expiration/cancellation release time |
| `fulfilled_at`| TIMESTAMP | YES | - | Consumption time on shipment |
| `release_reason`| VARCHAR(128)| YES | - | Reason code (`TTL_EXPIRED`, `USER_CANCELLED`) |

---

## 7. Order & OrderLine (`orders`, `order_lines`)
Commercial sales demand records.

### `orders`
- `order_id` (PK, `ORD-2026-000001`)
- `channel` (`ONLINE`, `RETAIL`, `MARKETPLACE`, `B2B`)
- `customer_reference` (Synthetic identifier)
- `order_status` (`PENDING`, `ALLOCATED`, `PARTIALLY_ALLOCATED`, `BACKORDERED`, `SHIPPED`, `DELIVERED`, `CANCELLED`)
- `order_date` (Timestamp)
- `requested_delivery_date` (Timestamp)
- `fulfillment_location_id` (FK `locations.location_id`)
- `total_amount` (Decimal)
- `currency` (Default `USD`)

### `order_lines`
- `order_line_id` (PK, `ORDL-2026-000001-01`)
- `order_id` (FK `orders.order_id`)
- `sku_id` (FK `skus.sku_id`)
- `ordered_quantity` (Integer)
- `allocated_quantity` (Integer)
- `fulfilled_quantity` (Integer)
- `unit_price` (Decimal)
- `line_status` (`PENDING`, `ALLOCATED`, `PARTIALLY_ALLOCATED`, `BACKORDERED`, `FULFILLED`, `CANCELLED`)

---

## 8. Shipment & ShipmentLine (`shipments`, `shipment_lines`)
Outbound transport documentation.

### `shipments`
- `shipment_id` (PK, `SHP-2026-000001`)
- `order_id` (FK `orders.order_id`)
- `origin_location_id` (FK `locations.location_id`)
- `destination_location_id` (FK `locations.location_id`, optional)
- `shipment_status` (`PENDING`, `SHIPPED`, `IN_TRANSIT`, `DELIVERED`, `CANCELLED`)
- `carrier` (`FedEx`, `UPS`, `DHL`, `InternalFleet`)
- `tracking_reference` (Carrier tracking code)
- `shipped_at`, `delivered_at` (Timestamps)

---

## 9. Transfer & TransferLine (`transfers`, `transfer_lines`)
Inter-facility multi-leg stock repositioning.

### `transfers`
- `transfer_id` (PK, `TRN-2026-000001`)
- `transfer_number` (Unique tracking reference)
- `source_location_id` (FK `locations.location_id`)
- `destination_location_id` (FK `locations.location_id`)
- `status` (`CREATED`, `APPROVED`, `DISPATCHED`, `IN_TRANSIT`, `RECEIVED`, `COMPLETED`, `CANCELLED`)
- `requested_at`, `dispatched_at`, `received_at` (Timestamps)
- `carrier`, `tracking_reference`, `notes`

---

## 10. ReplenishmentRule (`replenishment_rules`)
Automated min/max and lead-time safety inventory parameters.

- `rule_id` (PK, `RPL-000001`)
- `sku_id` (FK `skus.sku_id`)
- `location_id` (FK `locations.location_id`)
- `minimum_stock` (Integer)
- `maximum_stock` (Integer)
- `reorder_point` (Integer)
- `safety_stock` (Integer)
- `lead_time_days` (Integer)
- `reorder_quantity` (Integer)
- `inbound_eligibility_policy` (`ALLOW_CONFIRMED_IN_TRANSIT`, `ALLOW_ALL_IN_TRANSIT`, `STRICT_ON_HAND_ONLY`)
- `effective_from`, `effective_to` (Timestamps)
- `is_active` (Boolean)
