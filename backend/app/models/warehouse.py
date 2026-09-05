"""Warehouse SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.fulfillment_allocation import FulfillmentAllocation
    from app.models.inventory import Inventory


class Warehouse(Base):
    """
    Represents physical fulfillment warehouses/depot locations.
    """

    __tablename__ = "warehouses"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipping_cost_weight: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("1.00"), nullable=False
    )
    replenishment_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
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
    inventory_records: Mapped[List[Inventory]] = relationship(
        "Inventory", back_populates="warehouse"
    )
    fulfillment_allocations: Mapped[List[FulfillmentAllocation]] = relationship(
        "FulfillmentAllocation", back_populates="warehouse"
    )
