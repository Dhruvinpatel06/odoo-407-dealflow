"""SubscriptionPlan SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import BillingInterval, ProrationMethod
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.subscription import Subscription


class SubscriptionPlan(Base):
    """
    Configurable recurring billing plans.
    """

    __tablename__ = "subscription_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    billing_interval: Mapped[BillingInterval] = mapped_column(
        SAEnum(BillingInterval, name="billing_interval", native_enum=True),
        nullable=False,
    )
    interval_count: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )
    proration_method: Mapped[ProrationMethod] = mapped_column(
        SAEnum(ProrationMethod, name="proration_method", native_enum=True),
        nullable=False,
    )
    cancellation_policy: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    refund_policy: Mapped[str] = mapped_column(
        String(100), nullable=False
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
    subscriptions: Mapped[List[Subscription]] = relationship(
        "Subscription", back_populates="plan"
    )
