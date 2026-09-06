"""Billing repository layer for database persistence."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.common.enums import (
    BillingScheduleStatus,
    InvoiceStatus,
    InvoiceType,
    PaymentStatus,
)
from app.models.billing_schedule import BillingSchedule
from app.models.invoice import Invoice
from app.models.payment import Payment


class BillingRepository:
    """Handles persistence queries for Billing Schedules, Invoices, and Payments."""

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
    ) -> List[BillingSchedule]:
        """List billing schedule entries."""
        stmt = (
            select(BillingSchedule)
            .options(joinedload(BillingSchedule.subscription))
        )
        if subscription_id is not None:
            stmt = stmt.where(BillingSchedule.subscription_id == subscription_id)
        if status is not None:
            stmt = stmt.where(BillingSchedule.status == status)

        stmt = stmt.order_by(BillingSchedule.billing_date.asc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).unique().all())

    def get_schedule_by_id(
        self, db: Session, schedule_id: uuid.UUID
    ) -> Optional[BillingSchedule]:
        """Fetch billing schedule by UUID."""
        stmt = (
            select(BillingSchedule)
            .options(
                joinedload(BillingSchedule.subscription),
                joinedload(BillingSchedule.invoices),
            )
            .where(BillingSchedule.id == schedule_id)
        )
        return db.scalars(stmt).unique().first()

    def create_schedule(
        self, db: Session, schedule: BillingSchedule
    ) -> BillingSchedule:
        """Persist new billing schedule entry."""
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        return schedule

    def update_schedule(
        self, db: Session, schedule: BillingSchedule
    ) -> BillingSchedule:
        """Commit updates to a billing schedule."""
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        return schedule

    # =====================================================================
    # Invoices
    # =====================================================================

    def list_invoices(
        self,
        db: Session,
        order_id: Optional[uuid.UUID] = None,
        status: Optional[InvoiceStatus] = None,
        invoice_type: Optional[InvoiceType] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Invoice]:
        """List invoices with optional filters."""
        stmt = (
            select(Invoice)
            .options(
                joinedload(Invoice.order),
                joinedload(Invoice.billing_schedule),
            )
        )
        if order_id is not None:
            stmt = stmt.where(Invoice.order_id == order_id)
        if status is not None:
            stmt = stmt.where(Invoice.status == status)
        if invoice_type is not None:
            stmt = stmt.where(Invoice.invoice_type == invoice_type)

        stmt = stmt.order_by(Invoice.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).unique().all())

    def get_invoice_by_id(
        self, db: Session, invoice_id: uuid.UUID, for_update: bool = False
    ) -> Optional[Invoice]:
        """Fetch invoice by UUID with optional row locking."""
        stmt = (
            select(Invoice)
            .options(
                joinedload(Invoice.order),
                joinedload(Invoice.billing_schedule),
                joinedload(Invoice.payments),
            )
            .where(Invoice.id == invoice_id)
        )
        if for_update:
            stmt = stmt.with_for_update()
        return db.scalars(stmt).unique().first()

    def get_invoices_for_order(
        self, db: Session, order_id: uuid.UUID
    ) -> List[Invoice]:
        """Fetch all invoices belonging to an order."""
        stmt = (
            select(Invoice)
            .options(joinedload(Invoice.payments))
            .where(Invoice.order_id == order_id)
            .order_by(Invoice.created_at.asc())
        )
        return list(db.scalars(stmt).unique().all())


    def get_credit_notes_for_order(
        self, db: Session, order_id: uuid.UUID
    ) -> List[Invoice]:
        """Fetch credit notes for an order."""
        stmt = (
            select(Invoice)
            .where(
                Invoice.order_id == order_id,
                Invoice.invoice_type == InvoiceType.CREDIT_NOTE,
            )
            .order_by(Invoice.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    def create_invoice(self, db: Session, invoice: Invoice) -> Invoice:
        """Persist new invoice."""
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice

    def update_invoice(self, db: Session, invoice: Invoice) -> Invoice:
        """Commit updates to an existing invoice."""
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice

    # =====================================================================
    # Payments
    # =====================================================================

    def list_payments(
        self,
        db: Session,
        invoice_id: Optional[uuid.UUID] = None,
        status: Optional[PaymentStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Payment]:
        """List payments."""
        stmt = select(Payment).options(joinedload(Payment.invoice))
        if invoice_id is not None:
            stmt = stmt.where(Payment.invoice_id == invoice_id)
        if status is not None:
            stmt = stmt.where(Payment.status == status)

        stmt = stmt.order_by(Payment.payment_date.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def get_payment_by_id(
        self, db: Session, payment_id: uuid.UUID
    ) -> Optional[Payment]:
        """Fetch payment by UUID."""
        stmt = select(Payment).options(joinedload(Payment.invoice)).where(Payment.id == payment_id)
        return db.scalars(stmt).first()

    def get_payments_for_invoice(
        self, db: Session, invoice_id: uuid.UUID
    ) -> List[Payment]:
        """Get all payments applied to an invoice."""
        stmt = (
            select(Payment)
            .where(Payment.invoice_id == invoice_id)
            .order_by(Payment.payment_date.asc())
        )
        return list(db.scalars(stmt).all())

    def create_payment(self, db: Session, payment: Payment) -> Payment:
        """Persist new payment."""
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    def update_payment(self, db: Session, payment: Payment) -> Payment:
        """Commit updates to an existing payment."""
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment


billing_repository = BillingRepository()
