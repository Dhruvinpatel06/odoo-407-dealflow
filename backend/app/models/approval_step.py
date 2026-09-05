"""ApprovalStep SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import ApprovalStatus, ApproverRole
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.approval_instance import ApprovalInstance
    from app.models.user import User


class ApprovalStep(Base):
    """
    Represents each reviewer action within an approval instance.
    Sequential approval: when Finance is required, Manager step precedes Finance step.
    """

    __tablename__ = "approval_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    approval_instance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("approval_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    approver_role: Mapped[ApproverRole] = mapped_column(
        SAEnum(ApproverRole, name="approver_role", native_enum=True),
        nullable=False,
    )
    approver_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        SAEnum(ApprovalStatus, name="approval_status", native_enum=True),
        default=ApprovalStatus.PENDING,
        nullable=False,
        index=True,
    )
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(
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
    approval_instance: Mapped[ApprovalInstance] = relationship(
        "ApprovalInstance", back_populates="steps"
    )
    approver_user: Mapped[Optional[User]] = relationship(
        "User", back_populates="assigned_approval_steps"
    )
