"""Billing service layer orchestrating hybrid billing, invoices, schedules, and payments."""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.common.enums import (
    BillingInterval,
    BillingScheduleStatus,
    InvoiceStatus,
    InvoiceType,
    OrderStatus,
    PaymentStatus,
    ProrationMethod,
    SubscriptionStatus,
)
from app.core.exceptions import (
    BusinessRuleViolationError,
    InvalidStateTransitionError,
    ResourceNotFoundError,
)
from app.models.billing_schedule import BillingSchedule
from app.models.invoice import Invoice
from app.models.order import Order
from app.models.payment import Payment
from app.models.quotation_line import QuotationLine
from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.modules.audit.service import audit_service
from app.modules.billing.engine import billing_engine
from app.modules.billing.repository import billing_repository
from app.modules.billing.schemas import (
    BillingScheduleResponse,
    CreditNoteCreateRequest,
    InvoiceResponse,
    OrderBillingLineItem,
    OrderBillingResponse,
    PaymentCreateRequest,
    PaymentResponse,
)
from app.modules.subscriptions.engine import calculate_next_billing_date
from app.modules.subscriptions.repository import subscriptions_repository
from app.modules.subscriptions.schemas import SubscriptionResponse


class BillingService:
    """Coordinates hybrid billing, billing schedules, invoices, and payments."""

    # =====================================================================
    # Order Billing / Hybrid Billing
    # =====================================================================

    def _to_invoice_response(self, inv: Invoice) -> InvoiceResponse:
        """Map Invoice model to response schema."""
        balance_due = max(Decimal("0.00"), inv.total_amount - inv.paid_amount)
        return InvoiceResponse(
            id=inv.id,
            invoice_number=inv.invoice_number,
            order_id=inv.order_id,
            billing_schedule_id=inv.billing_schedule_id,
            invoice_type=inv.invoice_type,
            subtotal=inv.subtotal,
            tax_amount=inv.tax_amount,
            total_amount=inv.total_amount,
            paid_amount=inv.paid_amount,
            balance_due=balance_due,
            status=inv.status,
            due_date=inv.due_date,
            issued_at=inv.issued_at,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
        )

    def _to_payment_response(self, pay: Payment) -> PaymentResponse:
        """Map Payment model to response schema."""
        return PaymentResponse(
            id=pay.id,
            invoice_id=pay.invoice_id,
            amount=pay.amount,
            payment_method=pay.payment_method,
            transaction_reference=pay.transaction_reference,
            payment_date=pay.payment_date,
            status=pay.status,
            created_at=pay.created_at,
            updated_at=pay.updated_at,
        )

    def _to_schedule_response(self, sched: BillingSchedule) -> BillingScheduleResponse:
        """Map BillingSchedule model to response schema."""
        return BillingScheduleResponse(
            id=sched.id,
            subscription_id=sched.subscription_id,
            billing_date=sched.billing_date,
            amount=sched.amount,
            status=sched.status,
            proration_amount=sched.proration_amount,
            created_at=sched.created_at,
            updated_at=sched.updated_at,
        )

    def get_order_billing(self, db: Session, order_id: uuid.UUID) -> OrderBillingResponse:
        """Fetch complete billing overview for an order."""
        order = db.get(Order, order_id)
        if not order:
            raise ResourceNotFoundError("Order not found")

        lines = order.quotation.lines if order.quotation and order.quotation.lines else []
        one_time_items: List[OrderBillingLineItem] = []
        recurring_items: List[OrderBillingLineItem] = []

        for l in lines:
            item = OrderBillingLineItem(
                quotation_line_id=l.id,
                product_id=l.product_id,
                product_name=l.product.name if l.product else "Product",
                is_subscription=l.product.is_subscription if l.product else False,
                quantity=l.quantity,
                unit_price=l.unit_price,
                line_total=l.line_total,
            )
            if l.product and l.product.is_subscription:
                recurring_items.append(item)
            else:
                one_time_items.append(item)

        subscriptions = subscriptions_repository.list_subscriptions(db, order_id=order_id)
        invoices = billing_repository.get_invoices_for_order(db, order_id=order_id)

        # Totals calculation
        total_invoiced = sum(
            (inv.total_amount for inv in invoices if inv.invoice_type != InvoiceType.CREDIT_NOTE),
            Decimal("0.00"),
        )
        total_paid = sum(
            (inv.paid_amount for inv in invoices if inv.invoice_type != InvoiceType.CREDIT_NOTE),
            Decimal("0.00"),
        )
        balance_due = max(Decimal("0.00"), total_invoiced - total_paid)
        billing_complete = (
            len(invoices) > 0 and all(inv.status == InvoiceStatus.PAID for inv in invoices)
        )

        sub_responses = []
        for s in subscriptions:
            rec_amt = (s.quantity * s.unit_price).quantize(Decimal("0.01"))
            sub_responses.append(
                SubscriptionResponse(
                    id=s.id,
                    order_id=s.order_id,
                    quotation_line_id=s.quotation_line_id,
                    customer_id=s.customer_id,
                    customer_name=s.customer.name if s.customer else None,
                    product_id=s.product_id,
                    product_name=s.product.name if s.product else None,
                    plan_id=s.plan_id,
                    plan_name=s.plan.name if s.plan else None,
                    quantity=s.quantity,
                    unit_price=s.unit_price,
                    recurring_amount=rec_amt,
                    start_date=s.start_date,
                    next_billing_date=s.next_billing_date,
                    status=s.status,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
            )

        return OrderBillingResponse(
            order_id=order.id,
            order_number=order.order_number,
            order_status=order.status,
            one_time_lines=one_time_items,
            recurring_lines=recurring_items,
            subscriptions=sub_responses,
            invoices=[self._to_invoice_response(i) for i in invoices],
            total_amount=order.total_amount,
            total_invoiced=total_invoiced,
            total_paid=total_paid,
            balance_due=balance_due,
            billing_complete=billing_complete,
        )

    def generate_order_billing(
        self,
        db: Session,
        order_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> OrderBillingResponse:
        """
        Generate applicable billing artifacts for an order:
        - One-time lines produce an initial one-time invoice.
        - Recurring lines produce subscriptions and billing schedules.
        - Idempotent against duplicate invoice generation.
        """
        order = db.get(Order, order_id)
        if not order:
            raise ResourceNotFoundError("Order not found")

        if order.status == OrderStatus.CANCELLED:
            raise InvalidStateTransitionError("Cannot generate billing for a cancelled order")

        lines = order.quotation.lines if order.quotation and order.quotation.lines else []
        if not lines:
            raise BusinessRuleViolationError("Order has no commercial lines to bill")

        one_time_lines = [l for l in lines if not (l.product and l.product.is_subscription)]
        recurring_lines = [l for l in lines if (l.product and l.product.is_subscription)]

        now = datetime.datetime.now(datetime.timezone.utc)
        today = datetime.date.today()
        due_date = today + datetime.timedelta(days=30)

        # 1. One-time lines invoice generation (if not already generated)
        existing_invoices = billing_repository.get_invoices_for_order(db, order_id)
        has_one_time_invoice = any(
            inv.invoice_type == InvoiceType.ONE_TIME for inv in existing_invoices
        )

        if one_time_lines and not has_one_time_invoice:
            one_time_subtotal = sum((l.line_total for l in one_time_lines), Decimal("0.00"))
            one_time_tax = sum(
                ((l.line_total * l.product.tax_rate) / Decimal("100.00") if l.product else Decimal("0.00") for l in one_time_lines),
                Decimal("0.00"),
            ).quantize(Decimal("0.01"))
            one_time_total = (one_time_subtotal + one_time_tax).quantize(Decimal("0.01"))

            inv = Invoice(
                invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
                order_id=order_id,
                billing_schedule_id=None,
                invoice_type=InvoiceType.ONE_TIME,
                subtotal=one_time_subtotal,
                tax_amount=one_time_tax,
                total_amount=one_time_total,
                paid_amount=Decimal("0.00"),
                status=InvoiceStatus.ISSUED,
                due_date=due_date,
                issued_at=now,
            )
            db.add(inv)

        # 2. Recurring lines: generate Subscriptions and initial BillingSchedules
        if recurring_lines:
            active_plans = subscriptions_repository.list_plans(db, is_active=True)
            if not active_plans:
                # Create a default Monthly plan if none exists in catalog
                default_plan = SubscriptionPlan(
                    name="Standard Monthly Recurring",
                    billing_interval=BillingInterval.MONTHLY,
                    interval_count=1,
                    proration_method=ProrationMethod.DAILY_PRO_RATA,
                    cancellation_policy="IMMEDIATE",
                    refund_policy="PRO_RATA",
                    is_active=True,
                )
                db.add(default_plan)
                db.flush()
                active_plans = [default_plan]

            plan = active_plans[0]

            for rl in recurring_lines:
                existing_sub = subscriptions_repository.get_subscription_by_quotation_line_id(
                    db, rl.id
                )
                if not existing_sub:
                    next_bill_date = calculate_next_billing_date(
                        today, plan.billing_interval, plan.interval_count
                    )
                    sub = Subscription(
                        order_id=order_id,
                        quotation_line_id=rl.id,
                        customer_id=order.customer_id,
                        product_id=rl.product_id,
                        plan_id=plan.id,
                        quantity=rl.quantity,
                        unit_price=rl.unit_price,
                        start_date=today,
                        next_billing_date=next_bill_date,
                        status=SubscriptionStatus.ACTIVE,
                    )
                    db.add(sub)
                    db.flush()

                    recurring_amount = (rl.quantity * rl.unit_price).quantize(Decimal("0.01"))
                    sched = BillingSchedule(
                        subscription_id=sub.id,
                        billing_date=today,
                        amount=recurring_amount,
                        status=BillingScheduleStatus.SCHEDULED,
                        proration_amount=Decimal("0.00"),
                    )
                    db.add(sched)

        # Update order status if order was in CONFIRMED or FULFILLED
        if order.status in (OrderStatus.CONFIRMED, OrderStatus.FULFILLED):
            order.status = OrderStatus.BILLING
            db.add(order)

        db.commit()

        audit_service.log_event(
            db=db,
            entity_type="ORDER",
            entity_id=order.id,
            action="BILLING_GENERATE",
            user_id=current_user.id if current_user else None,
            new_values={"order_status": order.status.value},
        )

        return self.get_order_billing(db, order_id)

    # =====================================================================
    # Invoices Lifecycle
    # =====================================================================

    def list_invoices(
        self,
        db: Session,
        order_id: Optional[uuid.UUID] = None,
        status: Optional[InvoiceStatus] = None,
        invoice_type: Optional[InvoiceType] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[InvoiceResponse]:
        """List invoices with optional filters."""
        invoices = billing_repository.list_invoices(
            db, order_id=order_id, status=status, invoice_type=invoice_type, skip=skip, limit=limit
        )
        return [self._to_invoice_response(i) for i in invoices]

    def get_invoice(self, db: Session, invoice_id: uuid.UUID) -> InvoiceResponse:
        """Fetch invoice by UUID."""
        inv = billing_repository.get_invoice_by_id(db, invoice_id)
        if not inv:
            raise ResourceNotFoundError("Invoice not found")
        return self._to_invoice_response(inv)

    def issue_invoice(
        self,
        db: Session,
        invoice_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> InvoiceResponse:
        """Transition invoice from DRAFT to ISSUED."""
        inv = billing_repository.get_invoice_by_id(db, invoice_id, for_update=True)
        if not inv:
            raise ResourceNotFoundError("Invoice not found")

        if inv.status != InvoiceStatus.DRAFT:
            raise InvalidStateTransitionError(
                f"Invoice in status {inv.status.value} cannot be issued"
            )

        inv.status = InvoiceStatus.ISSUED
        inv.issued_at = datetime.datetime.now(datetime.timezone.utc)
        updated = billing_repository.update_invoice(db, inv)

        audit_service.log_event(
            db=db,
            entity_type="INVOICE",
            entity_id=updated.id,
            action="ISSUE",
            user_id=current_user.id if current_user else None,
            new_values={"status": InvoiceStatus.ISSUED.value},
        )
        return self._to_invoice_response(updated)

    def cancel_invoice(
        self,
        db: Session,
        invoice_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> InvoiceResponse:
        """Cancel an unpaid invoice."""
        inv = billing_repository.get_invoice_by_id(db, invoice_id, for_update=True)
        if not inv:
            raise ResourceNotFoundError("Invoice not found")

        if inv.paid_amount > Decimal("0.00"):
            raise BusinessRuleViolationError(
                "Cannot cancel an invoice with recorded payments. Issue a refund or credit note instead."
            )

        if inv.status == InvoiceStatus.CANCELLED:
            raise InvalidStateTransitionError("Invoice is already cancelled")

        inv.status = InvoiceStatus.CANCELLED
        updated = billing_repository.update_invoice(db, inv)

        audit_service.log_event(
            db=db,
            entity_type="INVOICE",
            entity_id=updated.id,
            action="CANCEL",
            user_id=current_user.id if current_user else None,
            new_values={"status": InvoiceStatus.CANCELLED.value},
        )
        return self._to_invoice_response(updated)

    def create_credit_note(
        self,
        db: Session,
        order_id: uuid.UUID,
        request: CreditNoteCreateRequest,
        current_user: Optional[User] = None,
    ) -> InvoiceResponse:
        """Create explicit credit note against an order."""
        order = db.get(Order, order_id)
        if not order:
            raise ResourceNotFoundError("Order not found")

        credit_inv = Invoice(
            invoice_number=f"CN-{uuid.uuid4().hex[:8].upper()}",
            order_id=order_id,
            billing_schedule_id=None,
            invoice_type=InvoiceType.CREDIT_NOTE,
            subtotal=request.amount,
            tax_amount=Decimal("0.00"),
            total_amount=request.amount,
            paid_amount=Decimal("0.00"),
            status=InvoiceStatus.ISSUED,
            due_date=datetime.date.today(),
            issued_at=datetime.datetime.now(datetime.timezone.utc),
        )
        created = billing_repository.create_invoice(db, credit_inv)

        audit_service.log_event(
            db=db,
            entity_type="INVOICE",
            entity_id=created.id,
            action="CREDIT_NOTE_CREATE",
            user_id=current_user.id if current_user else None,
            new_values={
                "invoice_type": InvoiceType.CREDIT_NOTE.value,
                "amount": str(request.amount),
            },
            reason=request.reason,
        )
        return self._to_invoice_response(created)

    # =====================================================================
    # Billing Schedules
    # =====================================================================

    def list_schedules(
        self,
        db: Session,
        subscription_id: Optional[uuid.UUID] = None,
        status: Optional[BillingScheduleStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BillingScheduleResponse]:
        """List billing schedule events."""
        scheds = billing_repository.list_schedules(
            db, subscription_id=subscription_id, status=status, skip=skip, limit=limit
        )
        return [self._to_schedule_response(s) for s in scheds]

    def get_schedule(
        self, db: Session, schedule_id: uuid.UUID
    ) -> BillingScheduleResponse:
        """Get billing schedule entry by UUID."""
        sched = billing_repository.get_schedule_by_id(db, schedule_id)
        if not sched:
            raise ResourceNotFoundError("Billing schedule entry not found")
        return self._to_schedule_response(sched)

    def generate_invoice_from_schedule(
        self,
        db: Session,
        schedule_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> InvoiceResponse:
        """Generate recurring invoice from a scheduled billing event."""
        sched = billing_repository.get_schedule_by_id(db, schedule_id)
        if not sched:
            raise ResourceNotFoundError("Billing schedule entry not found")

        if sched.status != BillingScheduleStatus.SCHEDULED:
            raise InvalidStateTransitionError(
                f"Cannot generate invoice for schedule in status {sched.status.value}"
            )

        sub = sched.subscription
        order = sub.order

        now = datetime.datetime.now(datetime.timezone.utc)
        due_date = sched.billing_date + datetime.timedelta(days=30)

        inv = Invoice(
            invoice_number=f"INV-REC-{uuid.uuid4().hex[:8].upper()}",
            order_id=order.id,
            billing_schedule_id=sched.id,
            invoice_type=InvoiceType.RECURRING,
            subtotal=sched.amount,
            tax_amount=Decimal("0.00"),
            total_amount=sched.amount,
            paid_amount=Decimal("0.00"),
            status=InvoiceStatus.ISSUED,
            due_date=due_date,
            issued_at=now,
        )
        db.add(inv)

        sched.status = BillingScheduleStatus.INVOICED
        db.add(sched)

        # Progress subscription to next scheduled billing cycle
        plan = sub.plan
        next_date = calculate_next_billing_date(
            sub.next_billing_date, plan.billing_interval, plan.interval_count
        )
        sub.next_billing_date = next_date
        db.add(sub)

        # Schedule the next billing event
        next_sched = BillingSchedule(
            subscription_id=sub.id,
            billing_date=next_date,
            amount=(sub.quantity * sub.unit_price).quantize(Decimal("0.01")),
            status=BillingScheduleStatus.SCHEDULED,
            proration_amount=Decimal("0.00"),
        )
        db.add(next_sched)

        db.commit()
        db.refresh(inv)

        audit_service.log_event(
            db=db,
            entity_type="BILLING_SCHEDULE",
            entity_id=sched.id,
            action="GENERATE_INVOICE",
            user_id=current_user.id if current_user else None,
            new_values={
                "invoice_id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "amount": str(inv.total_amount),
            },
        )
        return self._to_invoice_response(inv)

    def cancel_schedule(
        self,
        db: Session,
        schedule_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> BillingScheduleResponse:
        """Cancel a scheduled billing event."""
        sched = billing_repository.get_schedule_by_id(db, schedule_id)
        if not sched:
            raise ResourceNotFoundError("Billing schedule entry not found")

        if sched.status != BillingScheduleStatus.SCHEDULED:
            raise InvalidStateTransitionError(
                f"Cannot cancel schedule in status {sched.status.value}"
            )

        sched.status = BillingScheduleStatus.CANCELLED
        updated = billing_repository.update_schedule(db, sched)

        audit_service.log_event(
            db=db,
            entity_type="BILLING_SCHEDULE",
            entity_id=updated.id,
            action="CANCEL",
            user_id=current_user.id if current_user else None,
            new_values={"status": BillingScheduleStatus.CANCELLED.value},
        )
        return self._to_schedule_response(updated)

    # =====================================================================
    # Payments Lifecycle
    # =====================================================================

    def list_payments(
        self,
        db: Session,
        invoice_id: Optional[uuid.UUID] = None,
        status: Optional[PaymentStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PaymentResponse]:
        """List payments."""
        payments = billing_repository.list_payments(
            db, invoice_id=invoice_id, status=status, skip=skip, limit=limit
        )
        return [self._to_payment_response(p) for p in payments]

    def get_payment(self, db: Session, payment_id: uuid.UUID) -> PaymentResponse:
        """Fetch payment by UUID."""
        pay = billing_repository.get_payment_by_id(db, payment_id)
        if not pay:
            raise ResourceNotFoundError("Payment not found")
        return self._to_payment_response(pay)

    def record_payment(
        self,
        db: Session,
        invoice_id: uuid.UUID,
        request: PaymentCreateRequest,
        current_user: Optional[User] = None,
    ) -> PaymentResponse:
        """
        Record a payment against an invoice:
        - Prevents overpayment.
        - Updates invoice paid amount.
        - Derives new invoice status (ISSUED, PARTIALLY_PAID, PAID).
        - If invoice was generated from a billing schedule, updates schedule when PAID.
        """
        inv = billing_repository.get_invoice_by_id(db, invoice_id, for_update=True)
        if not inv:
            raise ResourceNotFoundError("Invoice not found")

        if inv.status in (InvoiceStatus.CANCELLED, InvoiceStatus.DRAFT):
            raise InvalidStateTransitionError(
                f"Cannot apply payment to invoice in status {inv.status.value}"
            )

        # Validate overpayment bounds
        billing_engine.validate_payment_bounds(
            invoice_total=inv.total_amount,
            invoice_paid=inv.paid_amount,
            payment_amount=request.amount,
        )

        inv.paid_amount += request.amount
        inv.status = billing_engine.derive_invoice_status(
            total_amount=inv.total_amount,
            paid_amount=inv.paid_amount,
            is_issued=True,
        )

        # If recurring invoice is fully paid, update corresponding billing schedule
        if inv.status == InvoiceStatus.PAID and inv.billing_schedule_id:
            sched = db.get(BillingSchedule, inv.billing_schedule_id)
            if sched:
                sched.status = BillingScheduleStatus.PAID
                db.add(sched)

        db.add(inv)

        payment = Payment(
            invoice_id=invoice_id,
            amount=request.amount,
            payment_method=request.payment_method,
            transaction_reference=request.transaction_reference,
            status=PaymentStatus.RECORDED,
            payment_date=datetime.datetime.now(datetime.timezone.utc),
        )
        created_payment = billing_repository.create_payment(db, payment)

        # Check order completion
        order = inv.order
        all_invoices = billing_repository.get_invoices_for_order(db, order.id)
        if all(i.status == InvoiceStatus.PAID for i in all_invoices):
            if order.status == OrderStatus.BILLING:
                order.status = OrderStatus.COMPLETED
                db.add(order)
                db.commit()

        audit_service.log_event(
            db=db,
            entity_type="PAYMENT",
            entity_id=created_payment.id,
            action="RECORD",
            user_id=current_user.id if current_user else None,
            new_values={
                "invoice_id": str(invoice_id),
                "amount": str(created_payment.amount),
                "invoice_status": inv.status.value,
                "invoice_paid_amount": str(inv.paid_amount),
            },
        )
        return self._to_payment_response(created_payment)

    def refund_payment(
        self,
        db: Session,
        payment_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> PaymentResponse:
        """Refund a recorded payment and adjust invoice paid amount and status."""
        pay = billing_repository.get_payment_by_id(db, payment_id)
        if not pay:
            raise ResourceNotFoundError("Payment not found")

        if pay.status != PaymentStatus.RECORDED:
            raise InvalidStateTransitionError(
                f"Cannot refund payment in status {pay.status.value}"
            )

        pay.status = PaymentStatus.REFUNDED

        inv = billing_repository.get_invoice_by_id(db, pay.invoice_id, for_update=True)
        if inv:
            inv.paid_amount = max(Decimal("0.00"), inv.paid_amount - pay.amount)
            inv.status = billing_engine.derive_invoice_status(
                total_amount=inv.total_amount,
                paid_amount=inv.paid_amount,
                is_issued=True,
            )
            db.add(inv)

        updated_payment = billing_repository.update_payment(db, pay)

        audit_service.log_event(
            db=db,
            entity_type="PAYMENT",
            entity_id=updated_payment.id,
            action="REFUND",
            user_id=current_user.id if current_user else None,
            new_values={
                "payment_status": PaymentStatus.REFUNDED.value,
                "invoice_paid_amount": str(inv.paid_amount) if inv else "0",
            },
        )
        return self._to_payment_response(updated_payment)


billing_service = BillingService()
