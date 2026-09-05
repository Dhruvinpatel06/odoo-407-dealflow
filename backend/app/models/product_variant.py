"""ProductVariant SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.price_list_item import PriceListItem
    from app.models.product import Product
    from app.models.quotation_line import QuotationLine


class ProductVariant(Base):
    """
    Represents simple product variants such as Size=Large or Pack=10.
    """

    __tablename__ = "product_variants"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attribute_name: Mapped[str] = mapped_column(String(100), nullable=False)
    attribute_value: Mapped[str] = mapped_column(String(100), nullable=False)
    extra_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
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
    product: Mapped[Product] = relationship(
        "Product", back_populates="variants"
    )
    price_list_items: Mapped[List[PriceListItem]] = relationship(
        "PriceListItem", back_populates="variant"
    )
    quotation_lines: Mapped[List[QuotationLine]] = relationship(
        "QuotationLine", back_populates="variant"
    )
