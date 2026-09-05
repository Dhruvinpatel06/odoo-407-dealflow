"""Quotations Pydantic schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.common.enums import QuotationStatus


class QuotationResponse(BaseModel):
    """Response schema representing a quotation summary/list item."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quotation_number: str
    customer_id: uuid.UUID
    sales_rep_id: uuid.UUID
    status: QuotationStatus
    subtotal: Decimal
    discount_amount: Decimal
    order_discount_percent: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    total_cost: Decimal
    margin_amount: Decimal
    margin_percent: Decimal
    risk_score: Decimal
    approval_required: bool
    current_approval_level: Optional[str] = None
    sent_at: Optional[datetime] = None
    last_activity_at: datetime
    valid_until: Optional[date] = None
    created_at: datetime
    updated_at: datetime
