"""Backorder SQLAlchemy model."""

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

from app.common.enums import BackorderStatus
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.quotation_line import QuotationLine


class Backorder(Base):
    """
    Represents quantities that cannot currently be fulfilled because inventory is insufficient.
    """

    __tablename__ = "backorders"

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
    quantity_backordered: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    quantity_remaining: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    status: Mapped[BackorderStatus] = mapped_column(
        SAEnum(BackorderStatus, name="backorder_status", native_enum=True),
        default=BackorderStatus.OPEN,
        nullable=False,
        index=True,
    )
    consolidation_requested: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
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
        "Order", back_populates="backorders"
    )
    quotation_line: Mapped[QuotationLine] = relationship(
        "QuotationLine", back_populates="backorders"
    )
