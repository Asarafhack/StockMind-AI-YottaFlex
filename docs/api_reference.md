# StockMind AI — REST API Reference

The StockMind AI REST API adheres to OpenAPI 3.0 standards and exposes all operational services under `/api/v1`.

Interactive Swagger UI documentation is available at: `http://localhost:8000/docs`

---

## Endpoints Summary

### Health & System
- `GET /health` — Service healthcheck, database status, environment name.
- `GET /` — Root metadata and operational endpoints index.

### Products & SKUs
- `GET /api/v1/products` — Filter products by category, brand; pagination support.
- `POST /api/v1/products` — Register new product entity.
- `GET /api/v1/products/{product_id}` — Product record detail.
- `GET /api/v1/skus` — Search and filter SKUs by product, status, code, variant.
- `POST /api/v1/skus` — Register new SKU variant with cost and price.
- `GET /api/v1/skus/{sku_id}` — SKU variant details.

### Locations
- `GET /api/v1/locations` — Filter facility nodes by type (`Warehouse`, `Retail Store`, etc.).
- `POST /api/v1/locations` — Register new physical node or channel.
- `GET /api/v1/locations/{location_id}` — Node facility details.

### Inventory & ATP
- `GET /api/v1/inventory` — Searchable inventory table with status filters (`HEALTHY`, `LOW_STOCK`, `STOCKOUT`, `BLOCKED`).
- `GET /api/v1/inventory/{sku_id}/{location_id}` — Node balance item.
- `GET /api/v1/inventory/{sku_id}/{location_id}/atp` — Full ATP formula breakdown with source movements.
- `POST /api/v1/inventory/{sku_id}/{location_id}/reconcile` — Compares stored balance against movement ledger.
- `POST /api/v1/inventory/{sku_id}/{location_id}/compensate` — Creates compensating movement for any detected drift.
- `GET /api/v1/inventory/movements/all` — Append-only movement ledger history.
- `POST /api/v1/inventory/movements/record` — Records a new atomic inventory movement.

### Reservations
- `GET /api/v1/reservations` — List active, expired, or released reservations.
- `POST /api/v1/reservations` — Atomically reserve stock for an order line.
- `POST /api/v1/reservations/{reservation_id}/release` — Manually release reserved stock.
- `POST /api/v1/reservations/sweep-expired` — Sweep reservations past TTL and restore availability.

### Orders & Allocation
- `GET /api/v1/orders` — List customer orders with lines and statuses.
- `POST /api/v1/orders` — Create customer order with optional automated ATP allocation.
- `GET /api/v1/orders/{order_id}` — Order detail and lines.
- `POST /api/v1/orders/{order_id}/allocate` — Run deterministic location allocation for order.
- `POST /api/v1/orders/{order_id}/fulfill` — Ship order, consume reservations, and record outbound `SALE`.
- `GET /api/v1/orders/{order_id}/allocations` — Explainable allocation decisions.

### Transfers
- `GET /api/v1/transfers` — List inter-facility stock transfers.
- `POST /api/v1/transfers` — Create transfer request in `CREATED` state.
- `POST /api/v1/transfers/{transfer_id}/dispatch` — Dispatch transfer: deduct origin, increment in-transit.
- `POST /api/v1/transfers/{transfer_id}/receive` — Receive transfer: clear in-transit, credit destination on-hand.
- `POST /api/v1/transfers/{transfer_id}/cancel` — Cancel transfer before dispatch.

### Anomalies & Exceptions
- `GET /api/v1/anomalies` — List anomalies filtered by severity and status.
- `GET /api/v1/anomalies/{anomaly_id}` — Anomaly detail with expected/observed condition.
- `POST /api/v1/anomalies/scan` — Trigger full scan of all 4 mandatory anomaly scenarios.
- `POST /api/v1/anomalies/{anomaly_id}/acknowledge` — Mark anomaly acknowledged.
- `POST /api/v1/anomalies/{anomaly_id}/resolve` — Mark anomaly resolved with audit note.

### Analytics & Simulation
- `GET /api/v1/analytics/overview` — Executive KPI summary (stock, fulfillment, accuracy, anomalies).
- `GET /api/v1/analytics/charts/location-distribution` — Multi-facility stock distribution.
- `GET /api/v1/analytics/charts/category-distribution` — Category unit and monetary values.
- `GET /api/v1/analytics/what-if/simulate` — Non-destructive digital twin simulation.

### Data Generator & Quality
- `POST /api/v1/generator/jobs` — Launch background data generation job (`starter` / `full`).
- `GET /api/v1/generator/jobs/{job_id}` — Poll background job progress and record counts.
- `POST /api/v1/validation/run` — Run database integrity validation checks.
- `GET /api/v1/validation/reports` — Machine-readable validation report.
- `GET /api/v1/validation/exports/list` — List exported Parquet, CSV, and JSON files.
- `GET /api/v1/audit/logs` — Chronological audit ledger log.
