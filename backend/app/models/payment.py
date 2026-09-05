"""Payment SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import PaymentStatus
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class Payment(Base):
    """
    Records payments made against invoices.
    Invoice status calculation:
      paid_amount >= total_amount -> PAID
      paid_amount > 0 and paid_amount < total_amount -> PARTIALLY_PAID
      paid_amount = 0 after issuance -> ISSUED
    """

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("invoices.id"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(100), nullable=False)
    transaction_reference: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    payment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status", native_enum=True),
        default=PaymentStatus.RECORDED,
        nullable=False,
        index=True,
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
    invoice: Mapped[Invoice] = relationship(
        "Invoice", back_populates="payments"
    )
