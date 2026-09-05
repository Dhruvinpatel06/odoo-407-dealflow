"""ApprovalInstance SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import ApprovalStatus
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.approval_step import ApprovalStep
    from app.models.quotation import Quotation


class ApprovalInstance(Base):
    """
    Represents one actual approval workflow execution for a quotation.
    A quotation may have multiple approval instances because customer negotiation can cause re-approval.
    """

    __tablename__ = "approval_instances"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), nullable=False
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        SAEnum(ApprovalStatus, name="approval_status", native_enum=True),
        default=ApprovalStatus.PENDING,
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
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
    quotation: Mapped[Quotation] = relationship(
        "Quotation", back_populates="approval_instances"
    )
    steps: Mapped[List[ApprovalStep]] = relationship(
        "ApprovalStep",
        back_populates="approval_instance",
        cascade="all, delete-orphan",
        order_by="ApprovalStep.step_order",
    )
