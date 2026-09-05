"""CustomerTier SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.discount_rule import DiscountRule
    from app.models.price_list import PriceList


class CustomerTier(Base):
    """
    Configurable customer tiers used for pricing and discount governance.
    """

    __tablename__ = "customer_tiers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_discount_limit: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
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
    customers: Mapped[List[Customer]] = relationship(
        "Customer", back_populates="tier"
    )
    price_lists: Mapped[List[PriceList]] = relationship(
        "PriceList", back_populates="customer_tier"
    )
    discount_rules: Mapped[List[DiscountRule]] = relationship(
        "DiscountRule", back_populates="customer_tier"
    )
