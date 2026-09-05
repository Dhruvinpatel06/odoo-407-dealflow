"""ApprovalPolicy SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ApprovalPolicy(Base):
    """
    Defines configurable risk-score ranges and the approval levels required for those ranges.
    Approval policy is configuration; execution is represented by approval_instances and approval_steps.
    """

    __tablename__ = "approval_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    min_risk_score: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), nullable=False
    )
    max_risk_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 2), nullable=True
    )
    requires_manager: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    requires_finance: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
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
