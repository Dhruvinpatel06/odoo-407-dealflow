# DealFlow360 Business Rules Rule

- FastAPI is authoritative for all business decisions.
- Recalculate quotation pricing, totals, margin, risk, and approval state whenever relevant commercial data changes.
- Discount ceilings consider customer tier and product category; stricter applicable limits win for core behavior.
- Approval routing is automatic; Sales Rep does not manually choose whether approval is required.
- Manager precedes Finance when Finance is required.
- Finance must not appear or activate when policy does not require it.
- Negotiation changes affecting commercial terms trigger recalculation and a new approval instance when required.
- Inventory availability is `quantity_on_hand - quantity_reserved`.
- Invoice status remains consistent with paid_amount.
- Customer portal operations enforce customer ownership server-side.
- Important approvals, rejections, revisions, edits, negotiation decisions, and fulfillment overrides must be auditable.
