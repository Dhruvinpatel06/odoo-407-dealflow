---
name: dealflow-business-rules
description: Designs and implements DealFlow360 pricing, discount risk, approval, fulfillment, billing, negotiation, and deal-health rules as simple deterministic backend engines with tests.
---
# DealFlow360 Business Rules

Use when implementing a calculation/workflow whose exact formula is not prescribed.

Procedure:
1. Read the relevant requirement and API/schema sections.
2. Identify inputs, outputs, invariants, and state transitions.
3. Choose the simplest deterministic hackathon-suitable algorithm.
4. Document the choice near the implementation.
5. Keep calculations pure where practical.
6. Add boundary/failure-case tests.
7. Ensure the service invokes the engine inside the correct transaction.

Known implementation-decision areas:
- blended risk score
- warehouse optimization
- anomaly detection
- delivery slippage
- subscription proration

Do not present these choices as if they were prescribed by the original requirements.
