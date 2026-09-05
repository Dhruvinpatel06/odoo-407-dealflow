"""RecommendationRule SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import RecommendationType
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.product import Product


class RecommendationRule(Base):
    """
    Simple configurable upsell/cross-sell relationships used to rank suggestions.
    Advanced ML recommendation infrastructure is out of scope; rules provide deterministic ranking.
    """

    __tablename__ = "recommendation_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    source_product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )
    recommended_product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )
    rule_type: Mapped[RecommendationType] = mapped_column(
        SAEnum(RecommendationType, name="recommendation_type", native_enum=True),
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    promotion_tag: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    min_margin_percent: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    co_purchase_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 2), nullable=True
    )
    is_promoted: Mapped[bool] = mapped_column(
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
    source_product: Mapped[Product] = relationship(
        "Product",
        foreign_keys=[source_product_id],
        back_populates="source_recommendations",
    )
    recommended_product: Mapped[Product] = relationship(
        "Product",
        foreign_keys=[recommended_product_id],
        back_populates="target_recommendations",
    )
