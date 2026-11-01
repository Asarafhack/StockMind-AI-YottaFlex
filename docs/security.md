# StockMind AI — Enterprise Security & Reliability

## 1. Secrets Management
- All sensitive variables (`DATABASE_URL`, `SECRET_KEY`, `API_HOST`, `API_PORT`) are managed via environment variables and loaded via Pydantic Settings (`backend/app/core/config.py`).
- No passwords, production tokens, or database credentials are committed to version control.
- An `.env.example` template provides transparent setup instructions.

---

## 2. Injection Protection & Data Sanitization
- All database queries are constructed through **SQLAlchemy 2.0 Core and ORM parameterized expressions**.
- Raw string formatting inside SQL queries is strictly prohibited, preventing SQL injection vulnerabilities.
- Request payloads are validated through strongly-typed Pydantic schemas.

---

## 3. Concurrency Protection & Ledger Integrity
- Row-level versioning on `InventoryBalance` records prevents stale updates during concurrent allocations.
- Balance reconciliation and compensating movement creation run within transactional boundaries.
- SQLite strictly enforces foreign keys (`PRAGMA foreign_keys=ON;`) and WAL journaling.

---

## 4. Role-Based Access Control (RBAC) Taxonomy
The system specifies five least-privilege roles:
1. `ADMIN`: Full system configuration, seed data pipelines, database migrations.
2. `INVENTORY_MANAGER`: Inventory balance adjustments, compensating movements, policy updates.
3. `WAREHOUSE_OPERATOR`: Transfer dispatch/receipt, packing, physical counts.
4. `MERCHANDISING_ANALYST`: Read-only access to ATP Explorer, What-If simulator, and BI analytics.
5. `VIEWER`: Read-only audit log inspection.
