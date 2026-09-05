"""Catalog Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Product Category Schemas ---


class ProductCategoryCreateRequest(BaseModel):
    """Request schema for creating a product category."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Category name (e.g., Hardware, Services, Subscriptions).",
    )
    description: Optional[str] = Field(
        None,
        description="Optional category description.",
    )
    is_active: bool = Field(
        default=True,
        description="Whether category is active.",
    )


class ProductCategoryUpdateRequest(BaseModel):
    """Request schema for updating a product category."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Updated category name.",
    )
    description: Optional[str] = Field(
        None,
        description="Updated category description.",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Updated active status of the category.",
    )


class ProductCategoryResponse(BaseModel):
    """Response schema representing a product category."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Product Schemas ---


class ProductCreateRequest(BaseModel):
    """Request schema for creating a product or service."""

    category_id: uuid.UUID = Field(
        ...,
        description="UUID of the product category.",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Product or service name.",
    )
    description: Optional[str] = Field(
        None,
        description="Product description.",
    )
    sku: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique stock keeping unit identifier.",
    )
    unit: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unit of measurement (e.g., pcs, hours, licenses).",
    )
    base_price: Decimal = Field(
        ...,
        ge=0,
        description="Default selling price.",
    )
    cost_price: Decimal = Field(
        ...,
        ge=0,
        description="Product cost price used for margin calculations.",
    )
    tax_rate: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        le=100,
        description="Tax rate percentage (e.g., 18.00).",
    )
    is_subscription: bool = Field(
        default=False,
        description="Whether the product is recurring/subscription-based.",
    )
    is_active: bool = Field(
        default=True,
        description="Whether product is active.",
    )


class ProductUpdateRequest(BaseModel):
    """Request schema for updating a product or service."""

    category_id: Optional[uuid.UUID] = Field(
        None,
        description="Updated product category UUID.",
    )
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Updated product name.",
    )
    description: Optional[str] = Field(
        None,
        description="Updated product description.",
    )
    sku: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Updated SKU.",
    )
    unit: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Updated unit of measurement.",
    )
    base_price: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Updated base selling price.",
    )
    cost_price: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Updated cost price.",
    )
    tax_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Updated tax rate percentage.",
    )
    is_subscription: Optional[bool] = Field(
        None,
        description="Updated subscription flag.",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Updated active status.",
    )


class ProductResponse(BaseModel):
    """Response schema representing a product or service."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    name: str
    description: Optional[str] = None
    sku: str
    unit: str
    base_price: Decimal
    cost_price: Decimal
    tax_rate: Decimal
    is_subscription: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductDetailResponse(ProductResponse):
    """Response schema representing detailed product information including category."""

    category: Optional[ProductCategoryResponse] = None


# --- Product Variant Schemas ---


class ProductVariantCreateRequest(BaseModel):
    """Request schema for creating a product variant."""

    attribute_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Attribute name (e.g., Size, Color, Pack).",
    )
    attribute_value: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Attribute value (e.g., Large, Red, 10-Pack).",
    )
    extra_price: Decimal = Field(
        default=Decimal("0.00"),
        description="Price added to parent product base price.",
    )
    sku: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional variant-specific SKU.",
    )
    is_active: bool = Field(
        default=True,
        description="Whether variant is active.",
    )


class ProductVariantUpdateRequest(BaseModel):
    """Request schema for updating a product variant."""

    attribute_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Updated attribute name.",
    )
    attribute_value: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Updated attribute value.",
    )
    extra_price: Optional[Decimal] = Field(
        None,
        description="Updated extra price.",
    )
    sku: Optional[str] = Field(
        None,
        max_length=100,
        description="Updated variant-specific SKU.",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Updated active status.",
    )


class ProductVariantResponse(BaseModel):
    """Response schema representing a product variant."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    attribute_name: str
    attribute_value: str
    extra_price: Decimal
    sku: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Aliases for convention compatibility
ProductCategoryCreate = ProductCategoryCreateRequest
ProductCategoryUpdate = ProductCategoryUpdateRequest
ProductCreate = ProductCreateRequest
ProductUpdate = ProductUpdateRequest
ProductVariantCreate = ProductVariantCreateRequest
ProductVariantUpdate = ProductVariantUpdateRequest
