"""Catalog, Product Categories, and Products endpoints router."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.modules.catalog.schemas import (
    ProductCategoryCreateRequest,
    ProductCategoryResponse,
    ProductCategoryUpdateRequest,
    ProductCreateRequest,
    ProductDetailResponse,
    ProductResponse,
    ProductUpdateRequest,
    ProductVariantCreateRequest,
    ProductVariantResponse,
    ProductVariantUpdateRequest,
)
from app.modules.catalog.service import catalog_service

router = APIRouter()

category_router = APIRouter(prefix="/product-categories", tags=["product-categories"])
product_router = APIRouter(prefix="/products", tags=["products"])
variant_router = APIRouter(prefix="/variants", tags=["variants"])


# --- Product Category Endpoints ---


@category_router.get(
    "",
    response_model=List[ProductCategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Product Categories",
)
def list_product_categories(
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
) -> List[ProductCategoryResponse]:
    """
    List product/service categories.
    Used by catalog, quotation, discount-rule, and reporting screens.
    """
    categories = catalog_service.list_categories(
        db=db, is_active=is_active, skip=skip, limit=limit
    )
    return [ProductCategoryResponse.model_validate(c) for c in categories]


@category_router.post(
    "",
    response_model=ProductCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Product Category",
)
def create_product_category(
    request: ProductCategoryCreateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> ProductCategoryResponse:
    """
    Create a product/service category.
    Enforces Admin-only configuration authorization.
    """
    category = catalog_service.create_category(db=db, request=request)
    return ProductCategoryResponse.model_validate(category)


@category_router.get(
    "/{id}",
    response_model=ProductCategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Product Category Details",
)
def get_product_category(
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
) -> ProductCategoryResponse:
    """Return category details by UUID."""
    category = catalog_service.get_category_by_id(db=db, category_id=id)
    return ProductCategoryResponse.model_validate(category)


@category_router.patch(
    "/{id}",
    response_model=ProductCategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Product Category",
)
def update_product_category(
    id: uuid.UUID,
    request: ProductCategoryUpdateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> ProductCategoryResponse:
    """
    Update product/service category details.
    Enforces Admin-only configuration authorization.
    """
    category = catalog_service.update_category(
        db=db, category_id=id, request=request
    )
    return ProductCategoryResponse.model_validate(category)


@category_router.delete(
    "/{id}",
    response_model=ProductCategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate Product Category",
)
def delete_product_category(
    id: uuid.UUID,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> ProductCategoryResponse:
    """
    Deactivate a product category following logical-deactivation convention.
    Enforces Admin-only configuration authorization.
    """
    category = catalog_service.deactivate_category(db=db, category_id=id)
    return ProductCategoryResponse.model_validate(category)


# --- Product Endpoints ---


@product_router.get(
    "",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="List / Search Products",
)
def list_products(
    search: Optional[str] = None,
    category_id: Optional[uuid.UUID] = None,
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
) -> List[ProductResponse]:
    """
    List and search active or all products/services.
    Supports search (by name or SKU), category filtering, and active-status filtering.
    Used by quotation builder, catalog, and reporting screens.
    """
    products = catalog_service.list_products(
        db=db,
        search=search,
        category_id=category_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    return [ProductResponse.model_validate(p) for p in products]


@product_router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Product",
)
def create_product(
    request: ProductCreateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> ProductResponse:
    """
    Create a new product or service.
    Enforces Admin-only product management authorization.
    """
    product = catalog_service.create_product(db=db, request=request)
    return ProductResponse.model_validate(product)


@product_router.get(
    "/{id}",
    response_model=ProductDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Product Details",
)
def get_product(
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
) -> ProductDetailResponse:
    """
    Return complete product information required by quotation and pricing logic,
    including associated category details.
    """
    product = catalog_service.get_product_by_id(db=db, product_id=id)
    return ProductDetailResponse.model_validate(product)


@product_router.patch(
    "/{id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Product",
)
def update_product(
    id: uuid.UUID,
    request: ProductUpdateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> ProductResponse:
    """
    Update product details.
    Enforces Admin-only product management authorization.
    """
    product = catalog_service.update_product(
        db=db, product_id=id, request=request
    )
    return ProductResponse.model_validate(product)


@product_router.delete(
    "/{id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate Product",
)
def delete_product(
    id: uuid.UUID,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> ProductResponse:
    """
    Deactivate a product following logical-deactivation convention.
    Enforces Admin-only product management authorization.
    """
    product = catalog_service.deactivate_product(db=db, product_id=id)
    return ProductResponse.model_validate(product)


@product_router.post(
    "/{product_id}/variants",
    response_model=ProductVariantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Product Variant",
)
def create_product_variant(
    product_id: uuid.UUID,
    request: ProductVariantCreateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> ProductVariantResponse:
    """
    Create a new product variant for a product.
    Enforces Admin-only catalog management authorization.
    """
    variant = catalog_service.create_variant(
        db=db, product_id=product_id, request=request
    )
    return ProductVariantResponse.model_validate(variant)


@product_router.get(
    "/{id}/variants",
    response_model=List[ProductVariantResponse],
    status_code=status.HTTP_200_OK,
    summary="List Product Variants",
)
def list_product_variants(
    id: uuid.UUID,
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
) -> List[ProductVariantResponse]:
    """
    List variants belonging to a specific product.
    Accessible to internal roles.
    """
    variants = catalog_service.list_variants_for_product(
        db=db, product_id=id, is_active=is_active, skip=skip, limit=limit
    )
    return [ProductVariantResponse.model_validate(v) for v in variants]


# --- Product Variant Endpoints ---


@variant_router.get(
    "/{id}",
    response_model=ProductVariantResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Variant Details",
)
def get_variant(
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
) -> ProductVariantResponse:
    """Return product variant details by UUID."""
    variant = catalog_service.get_variant_by_id(db=db, variant_id=id)
    return ProductVariantResponse.model_validate(variant)


@variant_router.patch(
    "/{id}",
    response_model=ProductVariantResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Variant",
)
def update_variant(
    id: uuid.UUID,
    request: ProductVariantUpdateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> ProductVariantResponse:
    """
    Update product variant details.
    Enforces Admin-only catalog management authorization.
    """
    variant = catalog_service.update_variant(
        db=db, variant_id=id, request=request
    )
    return ProductVariantResponse.model_validate(variant)


@variant_router.delete(
    "/{id}",
    response_model=ProductVariantResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate Variant",
)
def delete_variant(
    id: uuid.UUID,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> ProductVariantResponse:
    """
    Deactivate a product variant following logical-deactivation convention.
    Enforces Admin-only catalog management authorization.
    """
    variant = catalog_service.deactivate_variant(db=db, variant_id=id)
    return ProductVariantResponse.model_validate(variant)


router.include_router(category_router)
router.include_router(product_router)
router.include_router(variant_router)
