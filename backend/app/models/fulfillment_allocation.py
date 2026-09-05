"""FulfillmentAllocation SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import FulfillmentAllocationStatus
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.quotation_line import QuotationLine
    from app.models.warehouse import Warehouse


class FulfillmentAllocation(Base):
    """
    Represents the warehouse-level allocation of an order line.
    """

    __tablename__ = "fulfillment_allocations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quotation_line_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("quotation_lines.id"),
        nullable=False,
        index=True,
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("warehouses.id"),
        nullable=False,
        index=True,
    )
    quantity_allocated: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    quantity_fulfilled: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    estimated_shipping_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    is_suggested: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_manual_override: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    status: Mapped[FulfillmentAllocationStatus] = mapped_column(
        SAEnum(
            FulfillmentAllocationStatus,
            name="fulfillment_allocation_status",
            native_enum=True,
        ),
        default=FulfillmentAllocationStatus.SUGGESTED,
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
        "Order", back_populates="fulfillment_allocations"
    )
    quotation_line: Mapped[QuotationLine] = relationship(
        "QuotationLine", back_populates="fulfillment_allocations"
    )
    warehouse: Mapped[Warehouse] = relationship(
        "Warehouse", back_populates="fulfillment_allocations"
    )
