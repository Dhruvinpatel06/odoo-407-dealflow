---
description: Run focused DealFlow360 backend verification for the current implementation.
---
# Verify DealFlow360 Backend

1. Inspect git diff/status.
2. Identify changed modules and corresponding business rules.
3. Run narrow relevant unit tests.
4. Run relevant API/integration tests.
5. Verify migrations if models/schema changed.
6. Verify authentication/authorization for affected endpoints, including token expiry, disabled-user rejection, and session revocation when auth is affected.
7. Exercise the applicable acceptance flow.
8. Report pass/fail results and unresolved issues.
