"""Fulfillment and Orders Pydantic schemas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.common.enums import OrderStatus


class OrderResponse(BaseModel):
    """Response schema representing an order summary/list item."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_number: str
    quotation_id: uuid.UUID
    customer_id: uuid.UUID
    status: OrderStatus
    total_amount: Decimal
    confirmed_at: datetime
    created_at: datetime
    updated_at: datetime
