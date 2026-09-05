"""DiscountRule SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.customer_tier import CustomerTier
    from app.models.product_category import ProductCategory


class DiscountRule(Base):
    """
    Stores configurable discount ceilings based on customer tier and/or product category.
    """

    __tablename__ = "discount_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    customer_tier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("customer_tiers.id"),
        nullable=True,
        index=True,
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("product_categories.id"),
        nullable=True,
        index=True,
    )
    max_discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
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
    customer_tier: Mapped[Optional[CustomerTier]] = relationship(
        "CustomerTier", back_populates="discount_rules"
    )
    category: Mapped[Optional[ProductCategory]] = relationship(
        "ProductCategory", back_populates="discount_rules"
    )
