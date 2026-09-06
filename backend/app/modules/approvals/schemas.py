"""Approval Policy Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ApprovalPolicyCreateRequest(BaseModel):
    """Request schema for creating a configurable approval policy."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable approval policy name.",
    )
    min_risk_score: Decimal = Field(
        ...,
        ge=Decimal("0.00"),
        description="Minimum risk score covered by policy.",
    )
    max_risk_score: Optional[Decimal] = Field(
        None,
        ge=Decimal("0.00"),
        description="Maximum risk score covered by policy; null indicates no upper bound.",
    )
    requires_manager: bool = Field(
        default=False,
        description="Indicates whether Sales Manager approval is required.",
    )
    requires_finance: bool = Field(
        default=False,
        description="Indicates whether Finance/Operations approval is required.",
    )
    priority: int = Field(
        default=0,
        ge=0,
        description="Policy evaluation precedence (higher number = higher priority).",
    )
    is_active: bool = Field(
        default=True,
        description="Whether policy participates in evaluation.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Policy name cannot be empty or whitespace only")
        return cleaned

    @field_validator("min_risk_score")
    @classmethod
    def validate_min_risk_score(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.00"):
            raise ValueError("min_risk_score must be greater than or equal to 0.00")
        return round(v, 2)

    @field_validator("max_risk_score")
    @classmethod
    def validate_max_risk_score(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v < Decimal("0.00"):
                raise ValueError("max_risk_score must be greater than or equal to 0.00")
            return round(v, 2)
        return v

    @model_validator(mode="after")
    def validate_policy_rules(self) -> "ApprovalPolicyCreateRequest":
        if self.max_risk_score is not None and self.max_risk_score < self.min_risk_score:
            raise ValueError(
                "max_risk_score must be greater than or equal to min_risk_score"
            )
        if self.requires_finance and not self.requires_manager:
            raise ValueError(
                "Finance approval requires Sales Manager approval in the sequence"
            )
        return self


class ApprovalPolicyUpdateRequest(BaseModel):
    """Request schema for updating an existing approval policy."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Updated approval policy name.",
    )
    min_risk_score: Optional[Decimal] = Field(
        None,
        ge=Decimal("0.00"),
        description="Updated minimum risk score.",
    )
    max_risk_score: Optional[Decimal] = Field(
        None,
        ge=Decimal("0.00"),
        description="Updated maximum risk score; null represents no upper bound.",
    )
    requires_manager: Optional[bool] = Field(
        None,
        description="Updated Sales Manager approval requirement.",
    )
    requires_finance: Optional[bool] = Field(
        None,
        description="Updated Finance/Operations approval requirement.",
    )
    priority: Optional[int] = Field(
        None,
        ge=0,
        description="Updated evaluation precedence.",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Updated active status.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Policy name cannot be empty or whitespace only")
            return cleaned
        return v

    @field_validator("min_risk_score")
    @classmethod
    def validate_min_risk_score(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v < Decimal("0.00"):
                raise ValueError("min_risk_score must be greater than or equal to 0.00")
            return round(v, 2)
        return v

    @field_validator("max_risk_score")
    @classmethod
    def validate_max_risk_score(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v < Decimal("0.00"):
                raise ValueError("max_risk_score must be greater than or equal to 0.00")
            return round(v, 2)
        return v


class ApprovalPolicyResponse(BaseModel):
    """Response schema representing a configured approval policy."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    min_risk_score: Decimal
    max_risk_score: Optional[Decimal] = None
    requires_manager: bool
    requires_finance: bool
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
