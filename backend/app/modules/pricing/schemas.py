"""Pricing and Price Lists Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# --- Price List Schemas ---


class PriceListCreateRequest(BaseModel):
    """Request schema for creating a price list."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Price list name.",
    )
    customer_tier_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional customer tier UUID associated with this price list.",
    )
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        description="ISO currency code (e.g. USD, EUR, INR).",
    )
    is_active: bool = Field(
        default=True,
        description="Whether price list is active.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Price list name cannot be empty or whitespace only")
        return clean

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        clean = v.strip().upper()
        if len(clean) != 3 or not clean.isalpha():
            raise ValueError("Currency must be a 3-letter alphabetic ISO code")
        return clean


class PriceListUpdateRequest(BaseModel):
    """Request schema for updating a price list."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Updated price list name.",
    )
    customer_tier_id: Optional[uuid.UUID] = Field(
        None,
        description="Updated associated customer tier UUID.",
    )
    currency: Optional[str] = Field(
        None,
        min_length=3,
        max_length=3,
        description="Updated ISO currency code.",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Updated active status.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if not clean:
                raise ValueError("Price list name cannot be empty or whitespace only")
            return clean
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            if len(clean) != 3 or not clean.isalpha():
                raise ValueError("Currency must be a 3-letter alphabetic ISO code")
            return clean
        return v


class PriceListResponse(BaseModel):
    """Response schema representing a price list."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    customer_tier_id: Optional[uuid.UUID] = None
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Price List Item Schemas ---


class PriceListItemCreateRequest(BaseModel):
    """Request schema for adding a product/variant price to a price list."""

    product_id: uuid.UUID = Field(
        ...,
        description="Product UUID.",
    )
    variant_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional product variant UUID.",
    )
    price: Decimal = Field(
        ...,
        ge=0,
        description="Override unit selling price in this price list.",
    )


class PriceListItemUpdateRequest(BaseModel):
    """Request schema for updating a price list item."""

    variant_id: Optional[uuid.UUID] = Field(
        None,
        description="Updated variant UUID.",
    )
    price: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Updated unit selling price.",
    )


class PriceListItemResponse(BaseModel):
    """Response schema representing a price list item."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    price_list_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    price: Decimal
    created_at: datetime
    updated_at: datetime


# --- Pricing Resolution Schemas ---


class PricingResolveRequest(BaseModel):
    """Request schema for authoritative price resolution."""

    product_id: uuid.UUID = Field(
        ...,
        description="Product UUID to resolve price for.",
    )
    variant_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional product variant UUID.",
    )
    customer_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional customer UUID for tier and price list resolution.",
    )
    customer_tier_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional customer tier UUID override.",
    )
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        description="Currency code for price resolution.",
    )
    price_list_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional explicit price list UUID override.",
    )


class PricingResolveResponse(BaseModel):
    """Response schema representing resolved authoritative pricing."""

    model_config = ConfigDict(from_attributes=True)

    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    price_list_id: Optional[uuid.UUID] = None
    currency: str
    base_price: Decimal
    variant_extra_price: Decimal = Decimal("0.00")
    resolved_unit_price: Decimal
    cost_price: Decimal
    pricing_source: str = Field(
        ...,
        description="Source of the resolved price (e.g., PRICE_LIST, BASE_CATALOG).",
    )


# Aliases for convention compatibility
PriceListCreate = PriceListCreateRequest
PriceListUpdate = PriceListUpdateRequest
PriceListItemCreate = PriceListItemCreateRequest
PriceListItemUpdate = PriceListItemUpdateRequest
