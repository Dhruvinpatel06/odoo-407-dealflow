"""NegotiationComment SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.quotation import Quotation
    from app.models.quotation_line import QuotationLine
    from app.models.user import User


class NegotiationComment(Base):
    """
    Stores customer/internal comments and line-level questions associated with a quotation.
    """

    __tablename__ = "negotiation_comments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quotation_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("quotation_lines.id"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    comment: Mapped[str] = mapped_column(Text, nullable=False)
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
        "Quotation", back_populates="negotiation_comments"
    )
    quotation_line: Mapped[Optional[QuotationLine]] = relationship(
        "QuotationLine", back_populates="negotiation_comments"
    )
    user: Mapped[User] = relationship(
        "User", back_populates="negotiation_comments"
    )
