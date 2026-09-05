"""Subscription SQLAlchemy model."""

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

from app.common.enums import SubscriptionStatus
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.billing_schedule import BillingSchedule
    from app.models.customer import Customer
    from app.models.order import Order
    from app.models.product import Product
    from app.models.quotation_line import QuotationLine
    from app.models.subscription_plan import SubscriptionPlan


class Subscription(Base):
    """
    Represents an actual recurring subscription created from a confirmed order.
    """

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )
    quotation_line_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("quotation_lines.id"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("subscription_plans.id"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_billing_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus, name="subscription_status", native_enum=True),
        default=SubscriptionStatus.ACTIVE,
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
    order: Mapped[Order] = relationship(
        "Order", back_populates="subscriptions"
    )
    quotation_line: Mapped[QuotationLine] = relationship(
        "QuotationLine", back_populates="subscriptions"
    )
    customer: Mapped[Customer] = relationship(
        "Customer", back_populates="subscriptions"
    )
    product: Mapped[Product] = relationship(
        "Product", back_populates="subscriptions"
    )
    plan: Mapped[SubscriptionPlan] = relationship(
        "SubscriptionPlan", back_populates="subscriptions"
    )
    billing_schedules: Mapped[List[BillingSchedule]] = relationship(
        "BillingSchedule", back_populates="subscription", cascade="all, delete-orphan"
    )
