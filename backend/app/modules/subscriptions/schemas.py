"""Subscriptions Pydantic schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.common.enums import SubscriptionStatus


class SubscriptionResponse(BaseModel):
    """Response schema representing a subscription summary/list item."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    quotation_line_id: uuid.UUID
    customer_id: uuid.UUID
    product_id: uuid.UUID
    plan_id: uuid.UUID
    quantity: Decimal
    unit_price: Decimal
    start_date: date
    next_billing_date: date
    status: SubscriptionStatus
    created_at: datetime
    updated_at: datetime
