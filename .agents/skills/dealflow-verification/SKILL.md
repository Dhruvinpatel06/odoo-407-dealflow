---
name: dealflow-verification
description: Verifies DealFlow360 backend work through focused tests, API checks, database checks, and end-to-end acceptance flows.
---
# DealFlow360 Verification

Use after implementing a feature or phase.

Procedure:
1. Inspect git diff/status.
2. Identify changed modules and business rules.
3. Run narrow relevant unit tests.
4. Run relevant API/integration tests.
5. Verify migrations when models/schema changed.
6. Verify auth/authorization for affected endpoints.
7. Exercise the applicable acceptance flow.
8. Report pass/fail results and unresolved issues.

Acceptance priorities:
- discount violation -> risk -> automatic approval
- sequential manager/finance approval
- fulfillment split/backorder
- hybrid one-time + recurring billing
- customer negotiation -> re-approval
- payment -> invoice status
