"""Discount Rules Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DiscountRuleCreateRequest(BaseModel):
    """Request schema for creating a configurable discount rule."""

    customer_tier_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional customer tier UUID condition.",
    )
    category_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional product category UUID condition.",
    )
    max_discount_percent: Decimal = Field(
        ...,
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        description="Maximum permitted discount percentage ceiling (0.00 to 100.00).",
    )
    priority: int = Field(
        default=0,
        ge=0,
        description="Rule precedence when multiple rules apply (higher integer = higher priority).",
    )
    is_active: bool = Field(
        default=True,
        description="Whether rule participates in evaluation.",
    )

    @field_validator("max_discount_percent")
    @classmethod
    def validate_discount_percent(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.00") or v > Decimal("100.00"):
            raise ValueError("max_discount_percent must be between 0.00 and 100.00")
        return round(v, 2)

    @model_validator(mode="after")
    def validate_at_least_one_condition(self) -> "DiscountRuleCreateRequest":
        if self.customer_tier_id is None and self.category_id is None:
            raise ValueError(
                "Discount rule must specify at least one condition: customer_tier_id or category_id"
            )
        return self


class DiscountRuleUpdateRequest(BaseModel):
    """Request schema for updating a configurable discount rule."""

    customer_tier_id: Optional[uuid.UUID] = Field(
        None,
        description="Updated customer tier UUID condition.",
    )
    category_id: Optional[uuid.UUID] = Field(
        None,
        description="Updated product category UUID condition.",
    )
    max_discount_percent: Optional[Decimal] = Field(
        None,
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        description="Updated maximum permitted discount percentage ceiling (0.00 to 100.00).",
    )
    priority: Optional[int] = Field(
        None,
        ge=0,
        description="Updated rule precedence.",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Updated active status.",
    )

    @field_validator("max_discount_percent")
    @classmethod
    def validate_discount_percent(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v < Decimal("0.00") or v > Decimal("100.00"):
                raise ValueError("max_discount_percent must be between 0.00 and 100.00")
            return round(v, 2)
        return v


class DiscountRuleResponse(BaseModel):
    """Response schema representing a configured discount rule."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_tier_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    max_discount_percent: Decimal
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DiscountGovernanceResult(BaseModel):
    """Result of discount governance and limit resolution for a quotation line."""

    model_config = ConfigDict(from_attributes=True)

    requested_discount_percent: Decimal = Field(
        ...,
        description="Discount percentage requested on the quotation line.",
    )
    allowed_discount_percent: Decimal = Field(
        ...,
        description="Authoritative maximum discount percentage allowed under governance rules.",
    )
    applicable_discount_limit: Optional[Decimal] = Field(
        None,
        description="Applicable discount ceiling from configured rules (None if unrestricted/no rule).",
    )
    discount_excess_percent: Decimal = Field(
        default=Decimal("0.00"),
        description="Excess discount beyond the applicable ceiling: max(requested - limit, 0).",
    )
    is_violation: bool = Field(
        default=False,
        description="Whether requested discount strictly exceeds the applicable ceiling.",
    )
    has_applicable_rule: bool = Field(
        default=False,
        description="Whether any active discount rule was applicable to the line.",
    )

    # Traceability & context metadata
    applied_rule_id: Optional[uuid.UUID] = Field(
        None,
        description="UUID of the winning discount rule that determined the applicable limit.",
    )
    applied_rule_type: Optional[str] = Field(
        None,
        description="Scope type of the winning rule: 'TIER', 'CATEGORY', 'TIER_AND_CATEGORY', or None.",
    )
    tier_rule_limit: Optional[Decimal] = Field(
        None,
        description="Ceiling from the highest-priority applicable tier-specific rule, if present.",
    )
    category_rule_limit: Optional[Decimal] = Field(
        None,
        description="Ceiling from the highest-priority applicable category-specific rule, if present.",
    )
    applied_tier_id: Optional[uuid.UUID] = Field(
        None,
        description="Customer tier UUID evaluated in the governance check.",
    )
    applied_category_id: Optional[uuid.UUID] = Field(
        None,
        description="Product category UUID evaluated in the governance check.",
    )
    resolution_summary: str = Field(
        default="",
        description="Deterministic human-readable explanation of the rule resolution decision.",
    )
