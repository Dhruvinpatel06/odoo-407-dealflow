"""PriceListItem SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.price_list import PriceList
    from app.models.product import Product
    from app.models.product_variant import ProductVariant


class PriceListItem(Base):
    """
    Stores individual product/variant prices within a price list.
    """

    __tablename__ = "price_list_items"
    __table_args__ = (
        Index("ix_price_list_items_list_product", "price_list_id", "product_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    price_list_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("price_lists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("product_variants.id"),
        nullable=True,
        index=True,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
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
    price_list: Mapped[PriceList] = relationship(
        "PriceList", back_populates="items"
    )
    product: Mapped[Product] = relationship(
        "Product", back_populates="price_list_items"
    )
    variant: Mapped[Optional[ProductVariant]] = relationship(
        "ProductVariant", back_populates="price_list_items"
    )
