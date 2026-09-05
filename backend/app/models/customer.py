"""Customer SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.customer_tier import CustomerTier
    from app.models.negotiation_request import NegotiationRequest
    from app.models.order import Order
    from app.models.quotation import Quotation
    from app.models.subscription import Subscription
    from app.models.user import User


class Customer(Base):
    """
    Represents a B2B customer/account.
    """

    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    customer_tier_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("customer_tiers.id"),
        nullable=False,
        index=True,
    )
    billing_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipping_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
    tier: Mapped[CustomerTier] = relationship(
        "CustomerTier", back_populates="customers"
    )
    users: Mapped[List[User]] = relationship(
        "User", back_populates="customer", foreign_keys="User.customer_id"
    )
    quotations: Mapped[List[Quotation]] = relationship(
        "Quotation", back_populates="customer"
    )
    orders: Mapped[List[Order]] = relationship(
        "Order", back_populates="customer"
    )
    subscriptions: Mapped[List[Subscription]] = relationship(
        "Subscription", back_populates="customer"
    )
    negotiation_requests: Mapped[List[NegotiationRequest]] = relationship(
        "NegotiationRequest", back_populates="customer"
    )
