"""Subscriptions service layer orchestrating plans, subscription lifecycle, and proration."""

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
from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.modules.audit.service import audit_service
from app.modules.subscriptions.engine import (
    calculate_next_billing_date,
    subscriptions_engine,
)
from app.modules.subscriptions.repository import subscriptions_repository
from app.modules.subscriptions.schemas import (
    ProrationApplyRequest,
    ProrationPreviewRequest,
    ProrationPreviewResponse,
    SubscriptionCancelRequest,
    SubscriptionModifyRequest,
    SubscriptionPlanCreateRequest,
    SubscriptionPlanResponse,
    SubscriptionPlanUpdateRequest,
    SubscriptionResponse,
)


class SubscriptionsService:
    """Service layer for recurring subscription plans and subscriptions."""

    # =====================================================================
    # Subscription Plans
    # =====================================================================

    def list_plans(
        self,
        db: Session,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SubscriptionPlanResponse]:
        """List subscription plans."""
        plans = subscriptions_repository.list_plans(
            db, is_active=is_active, skip=skip, limit=limit
        )
        return [SubscriptionPlanResponse.model_validate(p) for p in plans]

    def get_plan(
        self, db: Session, plan_id: uuid.UUID
    ) -> SubscriptionPlanResponse:
        """Fetch subscription plan by UUID."""
        plan = subscriptions_repository.get_plan_by_id(db, plan_id)
        if not plan:
            raise ResourceNotFoundError("Subscription plan not found")
        return SubscriptionPlanResponse.model_validate(plan)

    def create_plan(
        self,
        db: Session,
        request: SubscriptionPlanCreateRequest,
        current_user: Optional[User] = None,
    ) -> SubscriptionPlanResponse:
        """Create a new recurring subscription plan."""
        plan = SubscriptionPlan(
            name=request.name,
            billing_interval=request.billing_interval,
            interval_count=request.interval_count,
            proration_method=request.proration_method,
            cancellation_policy=request.cancellation_policy,
            refund_policy=request.refund_policy,
            is_active=request.is_active,
        )
        created = subscriptions_repository.create_plan(db, plan)

        audit_service.log_event(
            db=db,
            entity_type="SUBSCRIPTION_PLAN",
            entity_id=created.id,
            action="CREATE",
            user_id=current_user.id if current_user else None,
            new_values={
                "name": created.name,
                "billing_interval": created.billing_interval.value,
                "proration_method": created.proration_method.value,
            },
        )
        return SubscriptionPlanResponse.model_validate(created)

    def update_plan(
        self,
        db: Session,
        plan_id: uuid.UUID,
        request: SubscriptionPlanUpdateRequest,
        current_user: Optional[User] = None,
    ) -> SubscriptionPlanResponse:
        """Update subscription plan configuration."""
        plan = subscriptions_repository.get_plan_by_id(db, plan_id)
        if not plan:
            raise ResourceNotFoundError("Subscription plan not found")

        old_values = {
            "name": plan.name,
            "billing_interval": plan.billing_interval.value,
            "is_active": plan.is_active,
        }

        if request.name is not None:
            plan.name = request.name
        if request.billing_interval is not None:
            plan.billing_interval = request.billing_interval
        if request.interval_count is not None:
            plan.interval_count = request.interval_count
        if request.proration_method is not None:
            plan.proration_method = request.proration_method
        if request.cancellation_policy is not None:
            plan.cancellation_policy = request.cancellation_policy
        if request.refund_policy is not None:
            plan.refund_policy = request.refund_policy
        if request.is_active is not None:
            plan.is_active = request.is_active

        updated = subscriptions_repository.update_plan(db, plan)

        audit_service.log_event(
            db=db,
            entity_type="SUBSCRIPTION_PLAN",
            entity_id=updated.id,
            action="UPDATE",
            user_id=current_user.id if current_user else None,
            old_values=old_values,
            new_values={
                "name": updated.name,
                "billing_interval": updated.billing_interval.value,
                "is_active": updated.is_active,
            },
        )
        return SubscriptionPlanResponse.model_validate(updated)

    def deactivate_plan(
        self,
        db: Session,
        plan_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> SubscriptionPlanResponse:
        """Deactivate a subscription plan."""
        plan = subscriptions_repository.get_plan_by_id(db, plan_id)
        if not plan:
            raise ResourceNotFoundError("Subscription plan not found")

        plan.is_active = False
        updated = subscriptions_repository.update_plan(db, plan)

        audit_service.log_event(
            db=db,
            entity_type="SUBSCRIPTION_PLAN",
            entity_id=updated.id,
            action="DEACTIVATE",
            user_id=current_user.id if current_user else None,
            new_values={"is_active": False},
        )
        return SubscriptionPlanResponse.model_validate(updated)

    # =====================================================================
    # Subscriptions Lifecycle
    # =====================================================================

    def _to_subscription_response(self, sub: Subscription) -> SubscriptionResponse:
        """Map Subscription model to API response schema."""
        recurring_amount = (sub.quantity * sub.unit_price).quantize(Decimal("0.01"))
        return SubscriptionResponse(
            id=sub.id,
            order_id=sub.order_id,
            quotation_line_id=sub.quotation_line_id,
            customer_id=sub.customer_id,
            customer_name=sub.customer.name if sub.customer else None,
            product_id=sub.product_id,
            product_name=sub.product.name if sub.product else None,
            plan_id=sub.plan_id,
            plan_name=sub.plan.name if sub.plan else None,
            quantity=sub.quantity,
            unit_price=sub.unit_price,
            recurring_amount=recurring_amount,
            start_date=sub.start_date,
            next_billing_date=sub.next_billing_date,
            status=sub.status,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
        )

    def list_subscriptions(
        self,
        db: Session,
        customer_id: Optional[uuid.UUID] = None,
        status: Optional[SubscriptionStatus] = None,
        order_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SubscriptionResponse]:
        """List subscriptions with optional filters."""
        subs = subscriptions_repository.list_subscriptions(
            db, customer_id=customer_id, status=status, order_id=order_id, skip=skip, limit=limit
        )
        return [self._to_subscription_response(s) for s in subs]

    def get_subscription(
        self, db: Session, subscription_id: uuid.UUID
    ) -> SubscriptionResponse:
        """Fetch subscription details by UUID."""
        sub = subscriptions_repository.get_subscription_by_id(db, subscription_id)
        if not sub:
            raise ResourceNotFoundError("Subscription not found")
        return self._to_subscription_response(sub)

    def preview_proration(
        self,
        db: Session,
        subscription_id: uuid.UUID,
        request: ProrationPreviewRequest,
    ) -> ProrationPreviewResponse:
        """Calculate non-mutating preview of mid-cycle proration adjustment."""
        sub = subscriptions_repository.get_subscription_by_id(db, subscription_id)
        if not sub:
            raise ResourceNotFoundError("Subscription not found")

        plan = sub.plan
        if request.new_plan_id:
            plan = subscriptions_repository.get_plan_by_id(db, request.new_plan_id) or plan

        new_qty = request.new_quantity if request.new_quantity is not None else sub.quantity
        new_price = request.new_unit_price if request.new_unit_price is not None else sub.unit_price

        res = subscriptions_engine.calculate_proration(
            current_quantity=sub.quantity,
            current_unit_price=sub.unit_price,
            new_quantity=new_qty,
            new_unit_price=new_price,
            start_date=sub.start_date,
            next_billing_date=sub.next_billing_date,
            proration_method=plan.proration_method,
            effective_date=request.effective_date,
        )

        return ProrationPreviewResponse(
            subscription_id=sub.id,
            current_amount=res.current_amount,
            new_amount=res.new_amount,
            days_remaining=res.days_remaining,
            total_period_days=res.total_period_days,
            proration_adjustment=res.proration_adjustment,
            proration_method=res.proration_method,
            description=res.description,
        )

    def apply_proration(
        self,
        db: Session,
        subscription_id: uuid.UUID,
        request: ProrationApplyRequest,
        current_user: Optional[User] = None,
    ) -> SubscriptionResponse:
        """Apply evaluated proration and modify subscription and billing records."""
        sub = subscriptions_repository.get_subscription_by_id(db, subscription_id)
        if not sub:
            raise ResourceNotFoundError("Subscription not found")

        if sub.status not in (SubscriptionStatus.ACTIVE, SubscriptionStatus.MODIFIED):
            raise InvalidStateTransitionError(
                f"Cannot apply proration to subscription in status {sub.status.value}"
            )

        new_qty = request.new_quantity if request.new_quantity is not None else sub.quantity
        new_price = request.new_unit_price if request.new_unit_price is not None else sub.unit_price
        new_plan_id = request.new_plan_id or sub.plan_id

        plan = subscriptions_repository.get_plan_by_id(db, new_plan_id)
        if not plan or not plan.is_active:
            raise BusinessRuleViolationError("Target subscription plan is invalid or inactive")

        proration = subscriptions_engine.calculate_proration(
            current_quantity=sub.quantity,
            current_unit_price=sub.unit_price,
            new_quantity=new_qty,
            new_unit_price=new_price,
            start_date=sub.start_date,
            next_billing_date=sub.next_billing_date,
            proration_method=plan.proration_method,
            effective_date=request.effective_date,
        )

        old_values = {
            "quantity": str(sub.quantity),
            "unit_price": str(sub.unit_price),
            "plan_id": str(sub.plan_id),
            "status": sub.status.value,
        }

        sub.quantity = new_qty
        sub.unit_price = new_price
        sub.plan_id = new_plan_id
        sub.status = SubscriptionStatus.MODIFIED

        # If adjustment is negative and credit note is requested -> create credit note invoice
        if proration.proration_adjustment < Decimal("0.00") and request.issue_credit_note:
            credit_amount = abs(proration.proration_adjustment)
            credit_inv = Invoice(
                invoice_number=f"CN-{uuid.uuid4().hex[:8].upper()}",
                order_id=sub.order_id,
                billing_schedule_id=None,
                invoice_type=InvoiceType.CREDIT_NOTE,
                subtotal=credit_amount,
                tax_amount=Decimal("0.00"),
                total_amount=credit_amount,
                paid_amount=Decimal("0.00"),
                status=InvoiceStatus.ISSUED,
                due_date=datetime.date.today(),
                issued_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db.add(credit_inv)

        # Update upcoming scheduled billing event amount if present
        for sched in sub.billing_schedules:
            if sched.status == BillingScheduleStatus.SCHEDULED:
                sched.amount = (new_qty * new_price).quantize(Decimal("0.01"))
                if proration.proration_adjustment > Decimal("0.00"):
                    sched.proration_amount += proration.proration_adjustment
                    sched.amount += proration.proration_adjustment
                db.add(sched)

        updated = subscriptions_repository.update_subscription(db, sub)

        audit_service.log_event(
            db=db,
            entity_type="SUBSCRIPTION",
            entity_id=updated.id,
            action="PRORATION_APPLY",
            user_id=current_user.id if current_user else None,
            old_values=old_values,
            new_values={
                "quantity": str(updated.quantity),
                "unit_price": str(updated.unit_price),
                "proration_adjustment": str(proration.proration_adjustment),
                "status": updated.status.value,
            },
        )
        return self._to_subscription_response(updated)

    def modify_subscription(
        self,
        db: Session,
        subscription_id: uuid.UUID,
        request: SubscriptionModifyRequest,
        current_user: Optional[User] = None,
    ) -> SubscriptionResponse:
        """Modify subscription terms with automatic proration application."""
        apply_req = ProrationApplyRequest(
            new_quantity=request.quantity,
            new_plan_id=request.plan_id,
            new_unit_price=request.unit_price,
            effective_date=request.effective_date,
            issue_credit_note=True,
        )
        return self.apply_proration(db, subscription_id, apply_req, current_user=current_user)

    def cancel_subscription(
        self,
        db: Session,
        subscription_id: uuid.UUID,
        request: SubscriptionCancelRequest,
        current_user: Optional[User] = None,
    ) -> SubscriptionResponse:
        """Cancel subscription, cancel future billing schedules, and optionally issue refund credit note."""
        sub = subscriptions_repository.get_subscription_by_id(db, subscription_id)
        if not sub:
            raise ResourceNotFoundError("Subscription not found")

        if sub.status == SubscriptionStatus.CANCELLED:
            raise InvalidStateTransitionError("Subscription is already cancelled")

        old_status = sub.status.value
        sub.status = SubscriptionStatus.CANCELLED

        # Cancel any upcoming scheduled billing events
        for sched in sub.billing_schedules:
            if sched.status == BillingScheduleStatus.SCHEDULED:
                sched.status = BillingScheduleStatus.CANCELLED
                db.add(sched)

        # Issue credit note for unused period if requested
        if request.issue_credit_note:
            refund_amount = subscriptions_engine.calculate_cancellation_refund(
                recurring_amount=sub.quantity * sub.unit_price,
                start_date=sub.start_date,
                next_billing_date=sub.next_billing_date,
            )
            if refund_amount > Decimal("0.00"):
                credit_inv = Invoice(
                    invoice_number=f"CN-{uuid.uuid4().hex[:8].upper()}",
                    order_id=sub.order_id,
                    billing_schedule_id=None,
                    invoice_type=InvoiceType.CREDIT_NOTE,
                    subtotal=refund_amount,
                    tax_amount=Decimal("0.00"),
                    total_amount=refund_amount,
                    paid_amount=Decimal("0.00"),
                    status=InvoiceStatus.ISSUED,
                    due_date=datetime.date.today(),
                    issued_at=datetime.datetime.now(datetime.timezone.utc),
                )
                db.add(credit_inv)

        updated = subscriptions_repository.update_subscription(db, sub)

        audit_service.log_event(
            db=db,
            entity_type="SUBSCRIPTION",
            entity_id=updated.id,
            action="CANCEL",
            user_id=current_user.id if current_user else None,
            old_values={"status": old_status},
            new_values={"status": SubscriptionStatus.CANCELLED.value},
            reason=request.reason,
        )
        return self._to_subscription_response(updated)

    def pause_subscription(
        self,
        db: Session,
        subscription_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> SubscriptionResponse:
        """Pause an active subscription."""
        sub = subscriptions_repository.get_subscription_by_id(db, subscription_id)
        if not sub:
            raise ResourceNotFoundError("Subscription not found")

        if sub.status not in (SubscriptionStatus.ACTIVE, SubscriptionStatus.MODIFIED):
            raise InvalidStateTransitionError(
                f"Cannot pause subscription in status {sub.status.value}"
            )

        sub.status = SubscriptionStatus.PAUSED
        updated = subscriptions_repository.update_subscription(db, sub)

        audit_service.log_event(
            db=db,
            entity_type="SUBSCRIPTION",
            entity_id=updated.id,
            action="PAUSE",
            user_id=current_user.id if current_user else None,
            new_values={"status": SubscriptionStatus.PAUSED.value},
        )
        return self._to_subscription_response(updated)

    def create_credit_note_for_subscription(
        self,
        db: Session,
        subscription_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> Invoice:
        """Explicitly issue a credit note for a subscription refund."""
        sub = subscriptions_repository.get_subscription_by_id(db, subscription_id)
        if not sub:
            raise ResourceNotFoundError("Subscription not found")

        refund_amount = subscriptions_engine.calculate_cancellation_refund(
            recurring_amount=sub.quantity * sub.unit_price,
            start_date=sub.start_date,
            next_billing_date=sub.next_billing_date,
        )
        if refund_amount <= Decimal("0.00"):
            raise BusinessRuleViolationError("No refundable balance remaining for this subscription")

        credit_inv = Invoice(
            invoice_number=f"CN-{uuid.uuid4().hex[:8].upper()}",
            order_id=sub.order_id,
            billing_schedule_id=None,
            invoice_type=InvoiceType.CREDIT_NOTE,
            subtotal=refund_amount,
            tax_amount=Decimal("0.00"),
            total_amount=refund_amount,
            paid_amount=Decimal("0.00"),
            status=InvoiceStatus.ISSUED,
            due_date=datetime.date.today(),
            issued_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(credit_inv)
        db.commit()
        db.refresh(credit_inv)

        audit_service.log_event(
            db=db,
            entity_type="INVOICE",
            entity_id=credit_inv.id,
            action="CREDIT_NOTE_CREATE",
            user_id=current_user.id if current_user else None,
            new_values={
                "invoice_type": InvoiceType.CREDIT_NOTE.value,
                "total_amount": str(refund_amount),
            },
        )
        return credit_inv


subscriptions_service = SubscriptionsService()
