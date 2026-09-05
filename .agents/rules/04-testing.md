# DealFlow360 Testing Rule

Prioritize tests for business correctness.

P0:
1. Discount governance
2. Blended risk
3. Automatic approval routing
4. Approval transitions
5. Warehouse split
6. Backorders
7. Subscription proration
8. Hybrid billing
9. Invoice/payment status
10. Negotiation re-approval

For every business-rule change:
- add/update unit tests
- add API/integration coverage when persistence or authorization is involved
- test invalid state transitions and unauthorized access
- run targeted tests first, then broader tests when practical
