"""Quotations Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import QuotationStatus


class QuotationLineResponse(BaseModel):
    """Response schema representing a quotation line snapshot."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quotation_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    line_total: Decimal
    unit_cost: Decimal
    margin_amount: Decimal
    margin_percent: Decimal
    allowed_discount_percent: Decimal
    discount_excess_percent: Decimal
    created_at: datetime
    updated_at: datetime


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


class QuotationDetailResponse(QuotationResponse):
    """Detailed quotation response including quotation lines and customer name."""

    lines: List[QuotationLineResponse] = Field(default_factory=list)
    customer_name: Optional[str] = None


class LineRiskDetail(BaseModel):
    """Authoritative line-level discount risk detail for UI explanation."""

    line_id: uuid.UUID
    product_id: uuid.UUID
    product_name: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    line_gross_value: Decimal
    requested_discount_percent: Decimal
    applicable_discount_limit: Optional[Decimal] = None
    allowed_discount_percent: Decimal
    discount_excess_percent: Decimal
    is_violation: bool
    has_applicable_rule: bool
    applied_rule_id: Optional[uuid.UUID] = None
    applied_rule_type: Optional[str] = None
    applied_tier_id: Optional[uuid.UUID] = None
    applied_category_id: Optional[uuid.UUID] = None
    resolution_summary: str


class QuotationRiskResponse(BaseModel):
    """Authoritative quotation discount-risk state representation."""

    quotation_id: uuid.UUID
    quotation_number: str
    subtotal: Decimal
    discount_amount: Decimal
    order_discount_percent: Decimal
    risk_score: Decimal
    approval_required: bool
    required_approval_level: Optional[str] = None
    total_lines_count: int
    violating_lines_count: int
    line_risks: List[LineRiskDetail]
    formula_explanation: str


class QuotationCreateRequest(BaseModel):
    """Request schema for creating a quotation."""

    customer_id: uuid.UUID
    valid_until: Optional[date] = None


class QuotationUpdateRequest(BaseModel):
    """Request schema for updating quotation metadata."""

    valid_until: Optional[date] = None


class QuotationLineCreateRequest(BaseModel):
    """Request schema for adding a line to a quotation."""

    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    quantity: Decimal = Field(..., gt=Decimal("0.00"))
    unit_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    discount_percent: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
    )
    tax_rate: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
    )
    description: Optional[str] = None


class QuotationLineUpdateRequest(BaseModel):
    """Request schema for modifying an existing quotation line."""

    quantity: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    unit_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    discount_percent: Optional[Decimal] = Field(
        None,
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
    )
    tax_rate: Optional[Decimal] = Field(
        None,
        ge=Decimal("0.00"),
    )
    description: Optional[str] = None


class QuotationRecalculateResponse(BaseModel):
    """Response returned upon explicit or triggered quotation recalculation."""

    quotation: QuotationDetailResponse
    risk: QuotationRiskResponse
    recalculated_at: datetime
