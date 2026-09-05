"""Invoice SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import InvoiceStatus, InvoiceType
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.billing_schedule import BillingSchedule
    from app.models.order import Order
    from app.models.payment import Payment


class Invoice(Base):
    """
    Represents one-time invoices, recurring invoices, and credit notes.
    One-time invoice: billing_schedule_id = NULL and invoice_type = ONE_TIME.
    Recurring invoice: billing_schedule_id references a schedule entry and invoice_type = RECURRING.
    Credit note: invoice_type = CREDIT_NOTE.
    """

    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    invoice_number: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )
    billing_schedule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("billing_schedules.id"),
        nullable=True,
        index=True,
    )
    invoice_type: Mapped[InvoiceType] = mapped_column(
        SAEnum(InvoiceType, name="invoice_type", native_enum=True),
        nullable=False,
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    status: Mapped[InvoiceStatus] = mapped_column(
        SAEnum(InvoiceStatus, name="invoice_status", native_enum=True),
        default=InvoiceStatus.DRAFT,
        nullable=False,
        index=True,
    )
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    issued_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    order: Mapped[Order] = relationship(
        "Order", back_populates="invoices"
    )
    billing_schedule: Mapped[Optional[BillingSchedule]] = relationship(
        "BillingSchedule", back_populates="invoices"
    )
    payments: Mapped[List[Payment]] = relationship(
        "Payment", back_populates="invoice", cascade="all, delete-orphan"
    )
