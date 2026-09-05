"""NegotiationRequest SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    JSON,
    Numeric,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import NegotiationRequestStatus
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.quotation import Quotation
    from app.models.user import User


class NegotiationRequest(Base):
    """
    Stores customer requests to change or renegotiate a quotation.
    When negotiation changes terms, FastAPI recalculates pricing, margin, risk, and approval requirements.
    """

    __tablename__ = "negotiation_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    requested_discount_percent: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    requested_changes: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[NegotiationRequestStatus] = mapped_column(
        SAEnum(
            NegotiationRequestStatus,
            name="negotiation_request_status",
            native_enum=True,
        ),
        default=NegotiationRequestStatus.SUBMITTED,
        nullable=False,
        index=True,
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
        "Quotation", back_populates="negotiation_requests"
    )
    customer: Mapped[Customer] = relationship(
        "Customer", back_populates="negotiation_requests"
    )
    requester: Mapped[User] = relationship(
        "User", back_populates="negotiation_requests"
    )
