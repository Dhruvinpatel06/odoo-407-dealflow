"""Customers Pydantic schemas."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CustomerTierCreateRequest(BaseModel):
    """Request schema for creating a customer tier."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Customer tier name (e.g., Bronze, Silver, Gold).",
    )
    description: Optional[str] = Field(
        None,
        description="Optional customer tier description.",
    )
    default_discount_limit: Decimal = Field(
        ...,
        ge=0,
        le=100,
        description="Default maximum discount percentage ceiling for the tier.",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the customer tier is active.",
    )


class CustomerTierUpdateRequest(BaseModel):
    """Request schema for updating a customer tier."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Updated customer tier name.",
    )
    description: Optional[str] = Field(
        None,
        description="Updated customer tier description.",
    )
    default_discount_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Updated default maximum discount percentage ceiling.",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Updated active status of the customer tier.",
    )


class CustomerTierResponse(BaseModel):
    """Response schema representing a customer tier."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    default_discount_limit: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CustomerCreate(BaseModel):
    """Request schema for creating a B2B customer."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Customer or company name.",
    )
    email: Optional[str] = Field(
        None,
        max_length=255,
        description="Primary customer contact email.",
    )
    phone: Optional[str] = Field(
        None,
        max_length=50,
        description="Primary customer contact phone.",
    )
    customer_tier_id: uuid.UUID = Field(
        ...,
        description="UUID of the associated customer tier.",
    )
    billing_address: Optional[str] = Field(
        None,
        description="Customer billing address.",
    )
    shipping_address: Optional[str] = Field(
        None,
        description="Default customer shipping address.",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the customer is active.",
    )


class CustomerUpdate(BaseModel):
    """Request schema for updating a B2B customer."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Updated customer or company name.",
    )
    email: Optional[str] = Field(
        None,
        max_length=255,
        description="Updated primary contact email.",
    )
    phone: Optional[str] = Field(
        None,
        max_length=50,
        description="Updated primary contact phone.",
    )
    customer_tier_id: Optional[uuid.UUID] = Field(
        None,
        description="Updated associated customer tier UUID.",
    )
    billing_address: Optional[str] = Field(
        None,
        description="Updated billing address.",
    )
    shipping_address: Optional[str] = Field(
        None,
        description="Updated default shipping address.",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Updated active status.",
    )


class CustomerResponse(BaseModel):
    """Response schema representing a B2B customer."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    customer_tier_id: uuid.UUID
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CustomerDetailResponse(CustomerResponse):
    """Response schema representing a detailed B2B customer record with associated tier."""

    tier: Optional[CustomerTierResponse] = None


class CustomerSearchParams(BaseModel):
    """Query parameters schema for searching/filtering customers."""

    search: Optional[str] = Field(
        None,
        description="Search term matching customer name, email, or phone.",
    )
    customer_tier_id: Optional[uuid.UUID] = Field(
        None,
        description="Filter by customer tier ID.",
    )
    is_active: Optional[bool] = Field(
        default=True,
        description="Filter by active status. Defaults to True (active customers only).",
    )
    skip: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip for pagination.",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=100,
        description="Maximum number of records to return.",
    )
