"""QuotationLine SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.backorder import Backorder
    from app.models.fulfillment_allocation import FulfillmentAllocation
    from app.models.negotiation_comment import NegotiationComment
    from app.models.product import Product
    from app.models.product_variant import ProductVariant
    from app.models.quotation import Quotation
    from app.models.subscription import Subscription


class QuotationLine(Base):
    """
    Individual products/services/subscriptions contained in a quotation.
    Serves as the commercial source for confirmed orders (no separate order_lines table).
    """

    __tablename__ = "quotation_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("quotations.id", ondelete="CASCADE"),
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
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    margin_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    margin_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    allowed_discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    discount_excess_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
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
        "Quotation", back_populates="lines"
    )
    product: Mapped[Product] = relationship(
        "Product", back_populates="quotation_lines"
    )
    variant: Mapped[Optional[ProductVariant]] = relationship(
        "ProductVariant", back_populates="quotation_lines"
    )
    fulfillment_allocations: Mapped[List[FulfillmentAllocation]] = relationship(
        "FulfillmentAllocation", back_populates="quotation_line"
    )
    backorders: Mapped[List[Backorder]] = relationship(
        "Backorder", back_populates="quotation_line"
    )
    subscriptions: Mapped[List[Subscription]] = relationship(
        "Subscription", back_populates="quotation_line"
    )
    negotiation_comments: Mapped[List[NegotiationComment]] = relationship(
        "NegotiationComment", back_populates="quotation_line"
    )
