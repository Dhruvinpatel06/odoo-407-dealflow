"""DealAlert SQLAlchemy model."""

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
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import DealAlertSeverity, DealAlertStatus, DealAlertType
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.quotation import Quotation


class DealAlert(Base):
    """
    Stores actionable deal-health/anomaly alerts.
    No separate deal_health table is created; deal health is derived from quotation activity,
    risk, fulfillment state, and alerts.
    """

    __tablename__ = "deal_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alert_type: Mapped[DealAlertType] = mapped_column(
        SAEnum(DealAlertType, name="deal_alert_type", native_enum=True),
        nullable=False,
        index=True,
    )
    severity: Mapped[DealAlertSeverity] = mapped_column(
        SAEnum(DealAlertSeverity, name="deal_alert_severity", native_enum=True),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metric_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    threshold_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    status: Mapped[DealAlertStatus] = mapped_column(
        SAEnum(DealAlertStatus, name="deal_alert_status", native_enum=True),
        default=DealAlertStatus.OPEN,
        nullable=False,
        index=True,
    )
    action_taken: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
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
        "Quotation", back_populates="deal_alerts"
    )
