"""Fulfillment, Warehouse, Inventory, and Backorders Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import (
    BackorderStatus,
    FulfillmentAllocationStatus,
    OrderStatus,
)


# =====================================================================
# Warehouse Schemas
# =====================================================================


class WarehouseCreateRequest(BaseModel):
    """Payload to create a fulfillment warehouse."""

    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    address: Optional[str] = None
    shipping_cost_weight: Decimal = Field(default=Decimal("1.00"), ge=Decimal("0.01"))
    replenishment_enabled: bool = False
    is_active: bool = True


class WarehouseUpdateRequest(BaseModel):
    """Payload to update an existing warehouse."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    address: Optional[str] = None
    shipping_cost_weight: Optional[Decimal] = Field(None, ge=Decimal("0.01"))
    replenishment_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class WarehouseResponse(BaseModel):
    """Warehouse response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    address: Optional[str] = None
    shipping_cost_weight: Decimal
    replenishment_enabled: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


# =====================================================================
# Inventory Schemas
# =====================================================================


class InventoryCreateRequest(BaseModel):
    """Payload to configure or initialize product stock in a warehouse."""

    product_id: uuid.UUID
    quantity_on_hand: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    reorder_level: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    reorder_quantity: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))


class InventoryUpdateRequest(BaseModel):
    """Payload to update stock quantities and replenishment configuration."""

    quantity_on_hand: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    quantity_reserved: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    reorder_level: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    reorder_quantity: Optional[Decimal] = Field(None, ge=Decimal("0.00"))


class InventoryResponse(BaseModel):
    """Single inventory record response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    warehouse_id: uuid.UUID
    product_id: uuid.UUID
    warehouse_name: Optional[str] = None
    warehouse_code: Optional[str] = None
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    quantity_on_hand: Decimal
    quantity_reserved: Decimal
    available_stock: Decimal
    reorder_level: Decimal
    reorder_quantity: Decimal
    updated_at: datetime


class ProductInventoryWarehouseItem(BaseModel):
    """Warehouse-level stock details for a product."""

    warehouse_id: uuid.UUID
    warehouse_name: str
    warehouse_code: str
    quantity_on_hand: Decimal
    quantity_reserved: Decimal
    available_stock: Decimal
    reorder_level: Decimal
    reorder_quantity: Decimal


class ProductInventoryResponse(BaseModel):
    """Aggregated product stock across all warehouses."""

    product_id: uuid.UUID
    product_name: str
    product_sku: str
    total_on_hand: Decimal
    total_reserved: Decimal
    total_available: Decimal
    warehouses: List[ProductInventoryWarehouseItem]


# =====================================================================
# Allocation Schemas
# =====================================================================


class AllocationResponse(BaseModel):
    """Warehouse allocation response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    quotation_line_id: uuid.UUID
    warehouse_id: uuid.UUID
    warehouse_name: Optional[str] = None
    warehouse_code: Optional[str] = None
    product_id: Optional[uuid.UUID] = None
    product_name: Optional[str] = None
    quantity_allocated: Decimal
    quantity_fulfilled: Decimal
    estimated_shipping_cost: Decimal
    is_suggested: bool
    is_manual_override: bool
    status: FulfillmentAllocationStatus
    created_at: datetime
    updated_at: datetime


class AllocationUpdateRequest(BaseModel):
    """Payload to adjust a single allocation."""

    warehouse_id: Optional[uuid.UUID] = None
    quantity_allocated: Optional[Decimal] = Field(None, gt=Decimal("0.00"))


class FulfillmentOverrideItem(BaseModel):
    """Single line allocation item for manual override."""

    quotation_line_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity_allocated: Decimal = Field(..., gt=Decimal("0.00"))


class FulfillmentOverrideRequest(BaseModel):
    """Payload to confirm complete manual warehouse allocation override."""

    allocations: List[FulfillmentOverrideItem] = Field(..., min_length=1)


# =====================================================================
# Backorder Schemas
# =====================================================================


class BackorderResponse(BaseModel):
    """Backorder response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    quotation_line_id: uuid.UUID
    product_id: Optional[uuid.UUID] = None
    product_name: Optional[str] = None
    quantity_backordered: Decimal
    quantity_remaining: Decimal
    status: BackorderStatus
    consolidation_requested: bool
    created_at: datetime
    updated_at: datetime


# =====================================================================
# Fulfillment Summary Schema
# =====================================================================


class FulfillmentSummaryResponse(BaseModel):
    """Complete order fulfillment state view."""

    order_id: uuid.UUID
    order_number: str
    order_status: OrderStatus
    allocations: List[AllocationResponse]
    backorders: List[BackorderResponse]
    total_quantity_required: Decimal
    total_quantity_allocated: Decimal
    total_quantity_fulfilled: Decimal
    total_quantity_backordered: Decimal
    estimated_shipment_count: int
    estimated_shipping_cost: Decimal
    is_split: bool


# Preserve OrderResponse for backward compatibility
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
