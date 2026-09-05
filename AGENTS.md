# DealFlow360 — Antigravity Project Context

## Mission
Build the DealFlow360 hackathon backend as a working, testable modular monolith within the hackathon time limit.

## Source of truth
Read these files before making architectural or domain changes:
- `docs/specs/DealFlow360_Requirements_and_Scope.txt`
- `docs/specs/DealFlow360_Database_Schema.txt`
- `docs/specs/DealFlow360_API_Endpoints.txt`
- `docs/specs/DealFlow360_Backend_Folder_Structure.txt`
- `docs/specs/DealFlow360_Tech_Stack_Updated.txt`
- Original problem statement: `docs/specs/DealFlow360.pdf`

Priority when sources conflict:
1. Explicit later user/project decision
2. Requirements & Scope
3. Database Schema
4. API Endpoints
5. Backend Folder Structure
6. Tech Stack

Do not silently change a finalized decision. If implementation exposes a conflict, stop and explain the conflict before changing the design.

## Final architecture
- Python + FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic
- PostgreSQL directly/self-managed
- Supabase Auth for authentication only
- REST/JSON
- Modular Monolith
- Pytest

Do NOT introduce Redis, Kafka, Celery, Kubernetes, GraphQL, microservices, a second auth system, Supabase-managed PostgreSQL, or Supabase Realtime as a core dependency.

## Backend architecture
Use:
Router -> Auth/Authorization -> Pydantic Schema -> Service -> Engine -> Repository -> SQLAlchemy Model -> PostgreSQL

- Routers are thin.
- Services coordinate business workflows and transactions.
- Engines contain reusable calculations.
- Repositories contain persistence/query logic.
- Models contain persistence mappings, not workflows.
- Core contains configuration, DB, security, dependencies, errors, and logging.
- Audit is cross-cutting and is invoked by business operations.

## Database invariants
The finalized schema has exactly 29 application tables.
- UUID primary keys.
- TIMESTAMPTZ for timestamps.
- NUMERIC for money/percentages/quantities.
- PostgreSQL enums for stable finite states.
- Quotation is the central commercial aggregate.
- `quotation_lines` remain the commercial source for confirmed orders.
- Do NOT create `order_lines`.
- Do NOT create `deal_health`, `reports`, `currencies`, `companies`, `shipping_methods`, or `refund_records` unless explicitly approved.
- Credit notes are invoices with `invoice_type=CREDIT_NOTE`.
- Approval configuration (`approval_policies`) is separate from execution (`approval_instances`, `approval_steps`).
- A quotation may have multiple approval instances because negotiation can trigger re-approval.

## Business authority
FastAPI is authoritative for:
- price resolution
- discount ceilings and risk
- margin
- approval routing/transitions
- recommendation eligibility/ranking
- warehouse allocation/backorders
- subscription proration
- billing/invoice status
- negotiation re-approval
- deal health/anomalies
- audit generation

Never trust frontend-supplied authoritative price, totals, margin, risk, approval state, inventory availability, invoice status, or customer ownership.

## Authentication and authorization
Supabase Auth owns credentials and authentication flows.
FastAPI must validate Supabase JWTs, resolve the application user, enforce role permissions, and enforce customer ownership on `/api/v1/portal/*`.
Never implement a second password/authentication system.

## Implementation behavior
Before coding:
1. Inspect the existing repository.
2. Read the relevant source-of-truth files.
3. Determine the smallest coherent change.
4. Preserve existing working behavior.
5. Implement in the correct architectural layer.
6. Add/update tests.
7. Run relevant formatting/lint/type/test commands available in the repo.
8. Report what changed, what was verified, and remaining risk.

Do not create speculative abstractions or unused files.

## Hackathon priority
1. Infrastructure/configuration
2. Database models + Alembic
3. Authentication/authorization
4. Configuration/catalog/pricing/discounts
5. Quotation calculations + discount risk
6. Automatic approval workflow
7. Fulfillment/backorders
8. Hybrid billing/payment
9. Customer portal + negotiation re-approval
10. Recommendations
11. Deal health
12. Reporting/export
13. Seed data + end-to-end verification

## Definition of done
A task is done only when implementation matches the source contract, relevant tests pass, database changes have migrations, important state transitions are validated server-side, audit behavior exists where required, no unrelated architecture drift was introduced, and the change is runnable.

## Current-task discipline
Work on one requested task at a time. Do not implement future phases unless required as a dependency.

When requirements leave an exact formula/algorithm unspecified, choose a simple deterministic hackathon-suitable rule, document it near the implementation, and add tests.

## Contract-change rule
If changing a finalized contract, explicitly identify affected requirement, affected DB/API contract, reason, and downstream impact before proceeding.
