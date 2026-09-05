---
name: dealflow-backend-implementation
description: Implements DealFlow360 FastAPI backend features while preserving the finalized modular-monolith architecture, API contract, database schema, authorization model, and business rules.
---
# DealFlow360 Backend Implementation

Use when implementing or modifying any DealFlow360 backend feature.

Procedure:
1. Read relevant finalized specs.
2. Inspect the current repository.
3. Identify endpoint/module/model involved.
4. Implement Router -> Schema -> Service -> Engine -> Repository -> Model as appropriate.
5. Preserve transaction boundaries and audit generation.
6. Add/update tests.
7. Run verification and report results.

Hard constraints:
- Do not invent endpoints when the contract already defines one.
- Do not add order_lines.
- Do not move business logic into route handlers.
- Do not trust frontend-calculated authoritative values.
- Do not bypass role/customer ownership checks.
- Do not alter finalized schema/API decisions without surfacing the conflict.
