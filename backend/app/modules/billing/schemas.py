"""Billing, Invoices, Billing Schedules, and Payments Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import (
    BillingScheduleStatus,
    InvoiceStatus,
    InvoiceType,
    OrderStatus,
    PaymentStatus,
)
from app.modules.subscriptions.schemas import SubscriptionResponse


# =====================================================================
# Billing Schedule Schemas
# =====================================================================


class BillingScheduleResponse(BaseModel):
    """Billing schedule entry schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subscription_id: uuid.UUID
    billing_date: date
    amount: Decimal
    status: BillingScheduleStatus
    proration_amount: Decimal
    created_at: datetime
    updated_at: datetime


# =====================================================================
# Invoice Schemas
# =====================================================================


class InvoiceResponse(BaseModel):
    """Invoice details schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_number: str
    order_id: uuid.UUID
    billing_schedule_id: Optional[uuid.UUID] = None
    invoice_type: InvoiceType
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    balance_due: Decimal = Decimal("0.00")
    status: InvoiceStatus
    due_date: Optional[date] = None
    issued_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CreditNoteCreateRequest(BaseModel):
    """Payload to create an explicit credit note against an order."""

    amount: Decimal = Field(..., gt=Decimal("0.00"))
    reason: Optional[str] = None


# =====================================================================
# Payment Schemas
# =====================================================================


class PaymentCreateRequest(BaseModel):
    """Payload to record a payment against an invoice."""

    amount: Decimal = Field(..., gt=Decimal("0.00"))
    payment_method: str = Field(..., min_length=1, max_length=100)
    transaction_reference: Optional[str] = Field(None, max_length=255)


class PaymentResponse(BaseModel):
    """Payment record details schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_id: uuid.UUID
    amount: Decimal
    payment_method: str
    transaction_reference: Optional[str] = None
    payment_date: datetime
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime


# =====================================================================
# Hybrid Order Billing View Schema
# =====================================================================


class OrderBillingLineItem(BaseModel):
    """Summary of a quotation line within the billing context."""

    quotation_line_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    is_subscription: bool
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class OrderBillingResponse(BaseModel):
    """Aggregated billing view for an order distinguishing one-time and recurring items."""

    order_id: uuid.UUID
    order_number: str
    order_status: OrderStatus
    one_time_lines: List[OrderBillingLineItem]
    recurring_lines: List[OrderBillingLineItem]
    subscriptions: List[SubscriptionResponse]
    invoices: List[InvoiceResponse]
    total_amount: Decimal
    total_invoiced: Decimal
    total_paid: Decimal
    balance_due: Decimal
    billing_complete: bool
