---
name: dealflow-database
description: Implements and verifies the DealFlow360 PostgreSQL, SQLAlchemy 2.x, and Alembic database layer against the finalized 30-table schema.
---
# DealFlow360 Database

Use when creating models, relationships, constraints, indexes, migrations, queries, or seed data.

Procedure:
1. Read `docs/specs/DealFlow360_Database_Schema.txt`.
2. Verify target entity and relationships.
3. Implement SQLAlchemy 2.x mappings.
4. Preserve UUID, TIMESTAMPTZ, NUMERIC, enum, uniqueness, FK, and index requirements.
5. Create an Alembic migration for schema changes.
6. Verify migration/schema state.
7. Add repository/integration tests for important constraints and queries.

Hard constraints:
- Exactly 30 finalized application tables unless explicitly changed; `auth_sessions` is the authentication session table.
- No order_lines, deal_health, reports, currencies, companies, shipping_methods, tax_rates, or refund_records by default.
- Money NUMERIC(12,2); percentages NUMERIC(5,2); quantities NUMERIC(12,2).
- Business calculations stay in FastAPI services/engines, not DB triggers.
