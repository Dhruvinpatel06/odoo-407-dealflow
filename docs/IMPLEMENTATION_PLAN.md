# DealFlow360 — Backend Implementation Plan

Complete in order unless a dependency requires otherwise.

## Phase 1 — Infrastructure
- [ ] Python environment/dependencies
- [ ] `.env.example`
- [ ] PostgreSQL connection
- [ ] SQLAlchemy 2.x
- [ ] FastAPI app
- [ ] exceptions/logging
- [ ] Supabase JWT verification
- [ ] role/customer authorization
- [ ] `/api/v1` router

## Phase 2 — Database
- [ ] All 29 SQLAlchemy models
- [ ] enums/relationships/constraints/indexes
- [ ] Initial Alembic migration
- [ ] Apply and verify migration

## Phase 3 — Identity + Configuration
- [ ] Auth `/auth/me`
- [ ] Users
- [ ] Customers/customer tiers
- [ ] Categories/products/variants
- [ ] Price lists/items
- [ ] Pricing resolution
- [ ] Discount rules
- [ ] Approval policies

## Phase 4 — Core Sales Workflow
- [ ] Quotation CRUD
- [ ] Quotation lines
- [ ] Pricing/totals/margin engine
- [ ] Discount ceiling engine
- [ ] Blended risk engine
- [ ] Automatic approval routing
- [ ] Sequential approval actions
- [ ] Audit generation
- [ ] Send/revision/confirm

## Phase 5 — Fulfillment
- [ ] Warehouses
- [ ] Inventory
- [ ] Warehouse split engine
- [ ] Allocation acceptance/override
- [ ] Backorders
- [ ] Fulfillment completion

## Phase 6 — Billing
- [ ] Subscription plans
- [ ] Subscriptions
- [ ] Proration preview/apply
- [ ] Billing schedules
- [ ] Hybrid billing generation
- [ ] Invoices
- [ ] Payments
- [ ] Invoice status
- [ ] Credit notes/refunds as scoped

## Phase 7 — Customer Workflow
- [ ] Portal quotation access
- [ ] Customer ownership enforcement
- [ ] Negotiation requests
- [ ] Comments
- [ ] Negotiation recalculation
- [ ] Automatic re-approval
- [ ] Customer confirmation

## Phase 8 — Supporting Features
- [ ] Recommendations
- [ ] Deal health
- [ ] Deal alerts
- [ ] Reporting
- [ ] PDF/XLS export
- [ ] Audit retrieval

## Phase 9 — Demo/Verification
- [ ] Deterministic seed data
- [ ] Discount violation demo
- [ ] Manager/Finance approval demo
- [ ] Warehouse split/backorder demo
- [ ] Hybrid billing demo
- [ ] Customer negotiation/re-approval demo
- [ ] Payment/invoice demo
- [ ] Full pytest suite
- [ ] Final API smoke test
