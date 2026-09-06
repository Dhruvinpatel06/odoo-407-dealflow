"""User SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import UserRole
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.approval_step import ApprovalStep
    from app.models.audit_log import AuditLog
    from app.models.auth_session import AuthSession
    from app.models.customer import Customer
    from app.models.negotiation_comment import NegotiationComment
    from app.models.negotiation_request import NegotiationRequest
    from app.models.quotation import Quotation


class User(Base):
    """
    Application user identity, authentication credentials, and authorization metadata.
    Owned by DealFlow360 manual authentication architecture.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", native_enum=True),
        nullable=False,
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
    )
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

    # Relationships
    customer: Mapped[Optional[Customer]] = relationship(
        "Customer", back_populates="user", foreign_keys=[customer_id]
    )
    auth_sessions: Mapped[List[AuthSession]] = relationship(
        "AuthSession", back_populates="user", cascade="all, delete-orphan"
    )
    assigned_approval_steps: Mapped[List[ApprovalStep]] = relationship(
        "ApprovalStep", back_populates="approver_user"
    )
    quotations: Mapped[List[Quotation]] = relationship(
        "Quotation", back_populates="sales_rep"
    )
    negotiation_requests: Mapped[List[NegotiationRequest]] = relationship(
        "NegotiationRequest", back_populates="requester"
    )
    negotiation_comments: Mapped[List[NegotiationComment]] = relationship(
        "NegotiationComment", back_populates="user"
    )
    audit_logs: Mapped[List[AuditLog]] = relationship(
        "AuditLog", back_populates="user"
    )
