"""Order SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import OrderStatus
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.backorder import Backorder
    from app.models.customer import Customer
    from app.models.fulfillment_allocation import FulfillmentAllocation
    from app.models.invoice import Invoice
    from app.models.quotation import Quotation
    from app.models.subscription import Subscription


class Order(Base):
    """
    Represents a confirmed sales order originating from a quotation.
    No separate order_lines table is created; quotation_lines remains the commercial line source.
    """

    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    order_number: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("quotations.id"),
        unique=True,
        index=True,
        nullable=False,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status", native_enum=True),
        default=OrderStatus.CONFIRMED,
        nullable=False,
        index=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
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
        "Quotation", back_populates="order"
    )
    customer: Mapped[Customer] = relationship(
        "Customer", back_populates="orders"
    )
    fulfillment_allocations: Mapped[List[FulfillmentAllocation]] = relationship(
        "FulfillmentAllocation", back_populates="order", cascade="all, delete-orphan"
    )
    backorders: Mapped[List[Backorder]] = relationship(
        "Backorder", back_populates="order", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[List[Subscription]] = relationship(
        "Subscription", back_populates="order"
    )
    invoices: Mapped[List[Invoice]] = relationship(
        "Invoice", back_populates="order"
    )
