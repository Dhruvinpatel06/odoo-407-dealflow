"""Subscription Plans and Subscriptions Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import BillingInterval, ProrationMethod, SubscriptionStatus


# =====================================================================
# Subscription Plan Schemas
# =====================================================================


class SubscriptionPlanCreateRequest(BaseModel):
    """Payload to create a recurring subscription plan."""

    name: str = Field(..., min_length=1, max_length=255)
    billing_interval: BillingInterval
    interval_count: int = Field(default=1, ge=1)
    proration_method: ProrationMethod = ProrationMethod.DAILY_PRO_RATA
    cancellation_policy: str = Field(default="IMMEDIATE", max_length=100)
    refund_policy: str = Field(default="PRO_RATA", max_length=100)
    is_active: bool = True


class SubscriptionPlanUpdateRequest(BaseModel):
    """Payload to update an existing subscription plan."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    billing_interval: Optional[BillingInterval] = None
    interval_count: Optional[int] = Field(None, ge=1)
    proration_method: Optional[ProrationMethod] = None
    cancellation_policy: Optional[str] = Field(None, max_length=100)
    refund_policy: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class SubscriptionPlanResponse(BaseModel):
    """Subscription plan details schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    billing_interval: BillingInterval
    interval_count: int
    proration_method: ProrationMethod
    cancellation_policy: str
    refund_policy: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# =====================================================================
# Subscription Schemas
# =====================================================================


class SubscriptionResponse(BaseModel):
    """Subscription details schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    quotation_line_id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: Optional[str] = None
    product_id: uuid.UUID
    product_name: Optional[str] = None
    plan_id: uuid.UUID
    plan_name: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    recurring_amount: Decimal = Decimal("0.00")
    start_date: date
    next_billing_date: date
    status: SubscriptionStatus
    created_at: datetime
    updated_at: datetime


class SubscriptionModifyRequest(BaseModel):
    """Payload to modify quantity, plan, or price for a subscription."""

    quantity: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    plan_id: Optional[uuid.UUID] = None
    unit_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    effective_date: Optional[date] = None


class SubscriptionCancelRequest(BaseModel):
    """Payload to cancel an active subscription."""

    reason: Optional[str] = None
    issue_credit_note: bool = False


# =====================================================================
# Proration Schemas
# =====================================================================


class ProrationPreviewRequest(BaseModel):
    """Payload to preview mid-cycle proration without persistent mutation."""

    new_quantity: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    new_plan_id: Optional[uuid.UUID] = None
    new_unit_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    effective_date: Optional[date] = None


class ProrationPreviewResponse(BaseModel):
    """Non-mutating calculation result of a proposed proration change."""

    subscription_id: uuid.UUID
    current_amount: Decimal
    new_amount: Decimal
    days_remaining: int
    total_period_days: int
    proration_adjustment: Decimal
    proration_method: ProrationMethod
    description: str


class ProrationApplyRequest(BaseModel):
    """Payload to apply evaluated proration to a subscription."""

    new_quantity: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    new_plan_id: Optional[uuid.UUID] = None
    new_unit_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    effective_date: Optional[date] = None
    issue_credit_note: bool = True
