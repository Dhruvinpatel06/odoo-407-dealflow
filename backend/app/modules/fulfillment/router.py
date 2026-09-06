"""Fulfillment API routers for Warehouses, Inventory, Allocations, and Backorders."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.common.enums import BackorderStatus, UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.modules.fulfillment.schemas import (
    AllocationResponse,
    AllocationUpdateRequest,
    BackorderResponse,
    FulfillmentOverrideRequest,
    FulfillmentSummaryResponse,
    InventoryCreateRequest,
    InventoryResponse,
    InventoryUpdateRequest,
    ProductInventoryResponse,
    WarehouseCreateRequest,
    WarehouseResponse,
    WarehouseUpdateRequest,
)
from app.modules.fulfillment.service import fulfillment_service

INTERNAL_ROLES = [
    UserRole.ADMIN,
    UserRole.FINANCE_OPERATIONS,
    UserRole.SALES_MANAGER,
    UserRole.SALES_REP,
]

OPS_ADMIN_ROLES = [
    UserRole.ADMIN,
    UserRole.FINANCE_OPERATIONS,
]

MANAGEMENT_ROLES = [
    UserRole.ADMIN,
    UserRole.FINANCE_OPERATIONS,
    UserRole.SALES_MANAGER,
]

# Separate routers matching spec conventions
warehouse_router = APIRouter(prefix="/warehouses", tags=["Warehouses"])
inventory_router = APIRouter(prefix="/inventory", tags=["Inventory"])
fulfillment_order_router = APIRouter(prefix="/orders", tags=["Fulfillment"])
backorder_router = APIRouter(prefix="/backorders", tags=["Backorders"])


# =====================================================================
# Warehouse Endpoints
# =====================================================================


@warehouse_router.get("", response_model=List[WarehouseResponse])
def list_warehouses(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> List[WarehouseResponse]:
    """List fulfillment warehouses."""
    return fulfillment_service.list_warehouses(
        db, is_active=is_active, skip=skip, limit=limit
    )


@warehouse_router.post(
    "", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED
)
def create_warehouse(
    request: WarehouseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(OPS_ADMIN_ROLES)),
) -> WarehouseResponse:
    """Create a new fulfillment warehouse."""
    return fulfillment_service.create_warehouse(
        db, request, current_user=current_user
    )


@warehouse_router.get("/{id}", response_model=WarehouseResponse)
def get_warehouse(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> WarehouseResponse:
    """Get warehouse details by UUID."""
    return fulfillment_service.get_warehouse(db, warehouse_id=id)


@warehouse_router.patch("/{id}", response_model=WarehouseResponse)
def update_warehouse(
    id: uuid.UUID,
    request: WarehouseUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(OPS_ADMIN_ROLES)),
) -> WarehouseResponse:
    """Update warehouse configuration."""
    return fulfillment_service.update_warehouse(
        db, warehouse_id=id, request=request, current_user=current_user
    )


@warehouse_router.delete("/{id}", response_model=WarehouseResponse)
def deactivate_warehouse(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(OPS_ADMIN_ROLES)),
) -> WarehouseResponse:
    """Deactivate warehouse (soft delete)."""
    return fulfillment_service.deactivate_warehouse(
        db, warehouse_id=id, current_user=current_user
    )


@warehouse_router.get(
    "/{warehouse_id}/inventory", response_model=List[InventoryResponse]
)
def get_warehouse_inventory(
    warehouse_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> List[InventoryResponse]:
    """Return inventory records for a specific warehouse."""
    return fulfillment_service.list_inventory(
        db, warehouse_id=warehouse_id, skip=skip, limit=limit
    )


@warehouse_router.post(
    "/{warehouse_id}/inventory",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def configure_warehouse_inventory(
    warehouse_id: uuid.UUID,
    request: InventoryCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(OPS_ADMIN_ROLES)),
) -> InventoryResponse:
    """Create or set inventory configuration for a product in warehouse."""
    return fulfillment_service.create_or_set_inventory(
        db, warehouse_id=warehouse_id, request=request, current_user=current_user
    )


# =====================================================================
# Inventory Endpoints
# =====================================================================


@inventory_router.get("", response_model=List[InventoryResponse])
def list_inventory(
    warehouse_id: Optional[uuid.UUID] = Query(None, description="Filter by warehouse"),
    product_id: Optional[uuid.UUID] = Query(None, description="Filter by product"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> List[InventoryResponse]:
    """List inventory records with optional warehouse and product filters."""
    return fulfillment_service.list_inventory(
        db, warehouse_id=warehouse_id, product_id=product_id, skip=skip, limit=limit
    )


@inventory_router.get("/{id}", response_model=InventoryResponse)
def get_inventory_record(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> InventoryResponse:
    """Return single inventory record by UUID."""
    return fulfillment_service.get_inventory(db, inventory_id=id)


@inventory_router.get(
    "/product/{product_id}", response_model=ProductInventoryResponse
)
def get_product_inventory(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> ProductInventoryResponse:
    """Return product inventory across all active warehouses with available stock."""
    return fulfillment_service.get_product_inventory(db, product_id=product_id)


@inventory_router.patch("/{id}", response_model=InventoryResponse)
def update_inventory(
    id: uuid.UUID,
    request: InventoryUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(OPS_ADMIN_ROLES)),
) -> InventoryResponse:
    """Update inventory quantities or replenishment configuration."""
    return fulfillment_service.update_inventory(
        db, inventory_id=id, request=request, current_user=current_user
    )


# =====================================================================
# Fulfillment Endpoints (/orders/{id}/fulfillment/*)
# =====================================================================


@fulfillment_order_router.get(
    "/{id}/fulfillment", response_model=FulfillmentSummaryResponse
)
def get_order_fulfillment(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> FulfillmentSummaryResponse:
    """Return complete order fulfillment state."""
    return fulfillment_service.get_order_fulfillment(db, order_id=id)


@fulfillment_order_router.post(
    "/{id}/fulfillment/suggest", response_model=FulfillmentSummaryResponse
)
def suggest_order_fulfillment(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> FulfillmentSummaryResponse:
    """Calculate recommended warehouse fulfillment split."""
    return fulfillment_service.suggest_fulfillment(db, order_id=id)


@fulfillment_order_router.post(
    "/{id}/fulfillment/accept", response_model=FulfillmentSummaryResponse
)
def accept_order_fulfillment(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(MANAGEMENT_ROLES)),
) -> FulfillmentSummaryResponse:
    """Accept the currently suggested warehouse split and reserve inventory."""
    return fulfillment_service.accept_fulfillment(
        db, order_id=id, current_user=current_user
    )


@fulfillment_order_router.get(
    "/{id}/fulfillment/allocations", response_model=List[AllocationResponse]
)
def get_order_allocations(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> List[AllocationResponse]:
    """Return all fulfillment allocations for an order."""
    summary = fulfillment_service.get_order_fulfillment(db, order_id=id)
    return summary.allocations


@fulfillment_order_router.patch(
    "/{id}/fulfillment/allocations/{allocation_id}",
    response_model=AllocationResponse,
)
def update_order_allocation(
    id: uuid.UUID,
    allocation_id: uuid.UUID,
    request: AllocationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(OPS_ADMIN_ROLES)),
) -> AllocationResponse:
    """Modify single allocation for manual fulfillment override."""
    return fulfillment_service.update_single_allocation(
        db,
        order_id=id,
        allocation_id=allocation_id,
        request=request,
        current_user=current_user,
    )


@fulfillment_order_router.post(
    "/{id}/fulfillment/override", response_model=FulfillmentSummaryResponse
)
def override_order_fulfillment(
    id: uuid.UUID,
    request: FulfillmentOverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(OPS_ADMIN_ROLES)),
) -> FulfillmentSummaryResponse:
    """Submit/confirm manual warehouse allocation override."""
    return fulfillment_service.override_fulfillment(
        db, order_id=id, request=request, current_user=current_user
    )


@fulfillment_order_router.post(
    "/{id}/fulfillment/complete", response_model=FulfillmentSummaryResponse
)
def complete_order_fulfillment(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(OPS_ADMIN_ROLES)),
) -> FulfillmentSummaryResponse:
    """Mark fulfillment completed and deduct inventory stock."""
    return fulfillment_service.complete_fulfillment(
        db, order_id=id, current_user=current_user
    )


@fulfillment_order_router.get(
    "/{id}/backorders", response_model=List[BackorderResponse]
)
def get_order_backorders(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> List[BackorderResponse]:
    """Return backorders belonging to an order."""
    return fulfillment_service.get_order_backorders(db, order_id=id)


# =====================================================================
# Backorder Endpoints (/backorders/*)
# =====================================================================


@backorder_router.get("", response_model=List[BackorderResponse])
def list_backorders(
    status: Optional[BackorderStatus] = Query(None, description="Filter by status"),
    order_id: Optional[uuid.UUID] = Query(None, description="Filter by order UUID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> List[BackorderResponse]:
    """List backorders with optional filters."""
    return fulfillment_service.list_backorders(
        db, status=status, order_id=order_id, skip=skip, limit=limit
    )


@backorder_router.get("/{id}", response_model=BackorderResponse)
def get_backorder(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> BackorderResponse:
    """Return backorder details by UUID."""
    return fulfillment_service.get_backorder(db, backorder_id=id)


@backorder_router.post("/{id}/consolidate", response_model=BackorderResponse)
def consolidate_backorder(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(OPS_ADMIN_ROLES)),
) -> BackorderResponse:
    """Consolidate remaining backordered quantity using newly available inventory."""
    return fulfillment_service.consolidate_backorder(
        db, backorder_id=id, current_user=current_user
    )


@backorder_router.post("/{id}/cancel", response_model=BackorderResponse)
def cancel_backorder(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(OPS_ADMIN_ROLES)),
) -> BackorderResponse:
    """Cancel open backorder."""
    return fulfillment_service.cancel_backorder(
        db, backorder_id=id, current_user=current_user
    )
