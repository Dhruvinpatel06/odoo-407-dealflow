"""BillingSchedule SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import BillingScheduleStatus
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.subscription import Subscription


class BillingSchedule(Base):
    """
    Stores recurring billing events/schedule entries generated for subscriptions.
    """

    __tablename__ = "billing_schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    billing_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[BillingScheduleStatus] = mapped_column(
        SAEnum(
            BillingScheduleStatus,
            name="billing_schedule_status",
            native_enum=True,
        ),
        default=BillingScheduleStatus.SCHEDULED,
        nullable=False,
        index=True,
    )
    proration_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
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
    subscription: Mapped[Subscription] = relationship(
        "Subscription", back_populates="billing_schedules"
    )
    invoices: Mapped[List[Invoice]] = relationship(
        "Invoice", back_populates="billing_schedule"
    )
