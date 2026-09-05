"""Product SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.inventory import Inventory
    from app.models.price_list_item import PriceListItem
    from app.models.product_category import ProductCategory
    from app.models.product_variant import ProductVariant
    from app.models.quotation_line import QuotationLine
    from app.models.recommendation_rule import RecommendationRule
    from app.models.subscription import Subscription


class Product(Base):
    """
    Main product/service catalog and source of base pricing/cost/margin data.
    """

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("product_categories.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sku: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    is_subscription: Mapped[bool] = mapped_column(
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
    category: Mapped[ProductCategory] = relationship(
        "ProductCategory", back_populates="products"
    )
    variants: Mapped[List[ProductVariant]] = relationship(
        "ProductVariant", back_populates="product", cascade="all, delete-orphan"
    )
    price_list_items: Mapped[List[PriceListItem]] = relationship(
        "PriceListItem", back_populates="product"
    )
    quotation_lines: Mapped[List[QuotationLine]] = relationship(
        "QuotationLine", back_populates="product"
    )
    inventory_records: Mapped[List[Inventory]] = relationship(
        "Inventory", back_populates="product"
    )
    subscriptions: Mapped[List[Subscription]] = relationship(
        "Subscription", back_populates="product"
    )
    source_recommendations: Mapped[List[RecommendationRule]] = relationship(
        "RecommendationRule",
        foreign_keys="RecommendationRule.source_product_id",
        back_populates="source_product",
    )
    target_recommendations: Mapped[List[RecommendationRule]] = relationship(
        "RecommendationRule",
        foreign_keys="RecommendationRule.recommended_product_id",
        back_populates="recommended_product",
    )
