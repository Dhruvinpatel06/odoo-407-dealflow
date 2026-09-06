"""Deterministic Billing Engine for calculations, status derivation, and overpayment checks."""

from __future__ import annotations

from decimal import Decimal

from app.common.enums import InvoiceStatus
from app.core.exceptions import BusinessRuleViolationError


class BillingEngine:
    """
    Deterministic billing calculations and validations:
    - Derive invoice status from paid_amount and total_amount.
    - Strict overpayment prevention.
    - Invoice subtotal and tax calculations.
    """

    def derive_invoice_status(
        self,
        total_amount: Decimal,
        paid_amount: Decimal,
        is_issued: bool = True,
    ) -> InvoiceStatus:
        """
        Calculates invoice status according to documented business rules:
        - paid_amount >= total_amount -> PAID
        - 0 < paid_amount < total_amount -> PARTIALLY_PAID
        - paid_amount = 0 after issuance -> ISSUED
        - paid_amount = 0 before issuance -> DRAFT
        """
        if total_amount <= Decimal("0.00"):
            return InvoiceStatus.PAID

        if paid_amount >= total_amount:
            return InvoiceStatus.PAID
        elif paid_amount > Decimal("0.00"):
            return InvoiceStatus.PARTIALLY_PAID
        else:
            return InvoiceStatus.ISSUED if is_issued else InvoiceStatus.DRAFT

    def validate_payment_bounds(
        self,
        invoice_total: Decimal,
        invoice_paid: Decimal,
        payment_amount: Decimal,
    ) -> None:
        """
        Ensures payment amount is strictly positive and will not cause overpayment.
        """
        if payment_amount <= Decimal("0.00"):
            raise BusinessRuleViolationError("Payment amount must be greater than zero")

        if invoice_paid + payment_amount > invoice_total:
            remaining_due = max(Decimal("0.00"), invoice_total - invoice_paid)
            raise BusinessRuleViolationError(
                f"Payment amount (${payment_amount}) exceeds remaining invoice balance (${remaining_due}). Overpayment is not permitted."
            )


billing_engine = BillingEngine()
