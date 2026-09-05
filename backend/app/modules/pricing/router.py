"""Pricing and Price Lists endpoints router."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.modules.pricing.schemas import (
    PriceListCreateRequest,
    PriceListItemCreateRequest,
    PriceListItemResponse,
    PriceListItemUpdateRequest,
    PriceListResponse,
    PriceListUpdateRequest,
    PricingResolveRequest,
    PricingResolveResponse,
)
from app.modules.pricing.service import pricing_service

router = APIRouter()

price_list_router = APIRouter(prefix="/price-lists", tags=["pricing"])
pricing_router = APIRouter(prefix="/pricing", tags=["pricing"])


# --- Price List Endpoints ---


@price_list_router.get(
    "",
    response_model=List[PriceListResponse],
    status_code=status.HTTP_200_OK,
    summary="List Price Lists",
)
def list_price_lists(
    customer_tier_id: Optional[uuid.UUID] = None,
    currency: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.SALES_REP,
                UserRole.FINANCE_OPERATIONS,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> List[PriceListResponse]:
    """List price lists with optional customer tier, currency, and active filters."""
    price_lists = pricing_service.list_price_lists(
        db=db,
        customer_tier_id=customer_tier_id,
        currency=currency,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    return [PriceListResponse.model_validate(p) for p in price_lists]


@price_list_router.post(
    "",
    response_model=PriceListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Price List",
)
def create_price_list(
    request: PriceListCreateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> PriceListResponse:
    """Create a new price list. Admin-only operation."""
    price_list = pricing_service.create_price_list(db=db, request=request)
    return PriceListResponse.model_validate(price_list)


@price_list_router.get(
    "/{id}",
    response_model=PriceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Price List Details",
)
def get_price_list(
    id: uuid.UUID,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.SALES_REP,
                UserRole.FINANCE_OPERATIONS,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> PriceListResponse:
    """Return price list details by UUID."""
    price_list = pricing_service.get_price_list_by_id(db=db, price_list_id=id)
    return PriceListResponse.model_validate(price_list)


@price_list_router.patch(
    "/{id}",
    response_model=PriceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Price List",
)
def update_price_list(
    id: uuid.UUID,
    request: PriceListUpdateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> PriceListResponse:
    """Update price list configuration. Admin-only operation."""
    price_list = pricing_service.update_price_list(
        db=db, price_list_id=id, request=request
    )
    return PriceListResponse.model_validate(price_list)


@price_list_router.delete(
    "/{id}",
    response_model=PriceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate Price List",
)
def delete_price_list(
    id: uuid.UUID,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> PriceListResponse:
    """Deactivate a price list following logical-deactivation convention."""
    price_list = pricing_service.deactivate_price_list(db=db, price_list_id=id)
    return PriceListResponse.model_validate(price_list)


# --- Price List Items Endpoints ---


@price_list_router.get(
    "/{id}/items",
    response_model=List[PriceListItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List Price List Items",
)
def list_price_list_items(
    id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.SALES_REP,
                UserRole.FINANCE_OPERATIONS,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> List[PriceListItemResponse]:
    """List product/variant prices within a price list."""
    items = pricing_service.list_items_for_price_list(
        db=db, price_list_id=id, skip=skip, limit=limit
    )
    return [PriceListItemResponse.model_validate(item) for item in items]


@price_list_router.post(
    "/{id}/items",
    response_model=PriceListItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Price List Item",
)
def create_price_list_item(
    id: uuid.UUID,
    request: PriceListItemCreateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> PriceListItemResponse:
    """Add product/variant pricing override to a price list."""
    item = pricing_service.create_price_list_item(
        db=db, price_list_id=id, request=request
    )
    return PriceListItemResponse.model_validate(item)


@price_list_router.patch(
    "/{id}/items/{item_id}",
    response_model=PriceListItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Price List Item",
)
def update_price_list_item(
    id: uuid.UUID,
    item_id: uuid.UUID,
    request: PriceListItemUpdateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> PriceListItemResponse:
    """Update a price list item price/configuration."""
    item = pricing_service.update_price_list_item(
        db=db, price_list_id=id, item_id=item_id, request=request
    )
    return PriceListItemResponse.model_validate(item)


@price_list_router.delete(
    "/{id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Price List Item",
)
def delete_price_list_item(
    id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> None:
    """Remove a price-list item."""
    pricing_service.delete_price_list_item(
        db=db, price_list_id=id, item_id=item_id
    )


# --- Pricing Resolution Endpoint ---


@pricing_router.post(
    "/resolve",
    response_model=PricingResolveResponse,
    status_code=status.HTTP_200_OK,
    summary="Resolve Authoritative Price",
)
def resolve_pricing(
    request: PricingResolveRequest,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.SALES_REP,
                UserRole.FINANCE_OPERATIONS,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> PricingResolveResponse:
    """
    Resolve authoritative selling price for a product/variant in a customer context.
    Never trusts frontend-supplied final unit prices.
    """
    return pricing_service.resolve_price(db=db, request=request)


router.include_router(price_list_router)
router.include_router(pricing_router)
