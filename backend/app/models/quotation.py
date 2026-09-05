"""Quotation SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
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

from app.common.enums import QuotationStatus
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.approval_instance import ApprovalInstance
    from app.models.customer import Customer
    from app.models.deal_alert import DealAlert
    from app.models.negotiation_comment import NegotiationComment
    from app.models.negotiation_request import NegotiationRequest
    from app.models.order import Order
    from app.models.quotation_line import QuotationLine
    from app.models.user import User


class Quotation(Base):
    """
    Central commercial document and core sales aggregate in DealFlow360.
    FastAPI recalculates persisted totals, margin, and risk snapshots whenever quotation data changes.
    """

    __tablename__ = "quotations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    quotation_number: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )
    sales_rep_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[QuotationStatus] = mapped_column(
        SAEnum(QuotationStatus, name="quotation_status", native_enum=True),
        default=QuotationStatus.DRAFT,
        nullable=False,
        index=True,
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    order_discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    margin_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    margin_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("0.00"), nullable=False
    )
    approval_required: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    current_approval_level: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False, index=True
    )
    valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
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
    customer: Mapped[Customer] = relationship(
        "Customer", back_populates="quotations"
    )
    sales_rep: Mapped[User] = relationship(
        "User", back_populates="quotations"
    )
    lines: Mapped[List[QuotationLine]] = relationship(
        "QuotationLine", back_populates="quotation", cascade="all, delete-orphan"
    )
    order: Mapped[Optional[Order]] = relationship(
        "Order", back_populates="quotation", uselist=False
    )
    approval_instances: Mapped[List[ApprovalInstance]] = relationship(
        "ApprovalInstance", back_populates="quotation", cascade="all, delete-orphan"
    )
    negotiation_requests: Mapped[List[NegotiationRequest]] = relationship(
        "NegotiationRequest", back_populates="quotation", cascade="all, delete-orphan"
    )
    negotiation_comments: Mapped[List[NegotiationComment]] = relationship(
        "NegotiationComment", back_populates="quotation", cascade="all, delete-orphan"
    )
    deal_alerts: Mapped[List[DealAlert]] = relationship(
        "DealAlert", back_populates="quotation", cascade="all, delete-orphan"
    )
