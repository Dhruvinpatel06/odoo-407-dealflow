"""Catalog service layer."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import DealFlowException, ResourceNotFoundError
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_variant import ProductVariant
from app.modules.catalog.repository import catalog_repository
from app.modules.catalog.schemas import (
    ProductCategoryCreateRequest,
    ProductCategoryUpdateRequest,
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductVariantCreateRequest,
    ProductVariantUpdateRequest,
)


class CatalogService:
    """Coordinates business logic and workflows for catalog entities."""

    # --- Product Category Operations ---

    def list_categories(
        self,
        db: Session,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ProductCategory]:
        """List product categories with optional active status filtering."""
        return catalog_repository.list_categories(
            db=db, is_active=is_active, skip=skip, limit=limit
        )

    def get_category_by_id(
        self, db: Session, category_id: uuid.UUID
    ) -> ProductCategory:
        """Fetch product category by id, ensuring existence."""
        category = catalog_repository.get_category_by_id(db, category_id)
        if not category:
            raise ResourceNotFoundError("Product category not found")
        return category

    def create_category(
        self, db: Session, request: ProductCategoryCreateRequest
    ) -> ProductCategory:
        """
        Create a new product category.
        Validates category name uniqueness and persists the category.
        """
        cleaned_name = request.name.strip()
        if not cleaned_name:
            raise DealFlowException("Category name cannot be empty", status_code=400)

        existing = catalog_repository.get_category_by_name(db, cleaned_name)
        if existing:
            raise DealFlowException(
                "A product category with this name already exists", status_code=400
            )

        return catalog_repository.create_category(
            db=db,
            name=cleaned_name,
            description=request.description,
            is_active=request.is_active,
        )

    def update_category(
        self,
        db: Session,
        category_id: uuid.UUID,
        request: ProductCategoryUpdateRequest,
    ) -> ProductCategory:
        """
        Update an existing product category.
        Validates existence, name uniqueness (if changed), and applies valid updates.
        """
        category = self.get_category_by_id(db, category_id)

        updates = request.model_dump(exclude_unset=True)
        if not updates:
            return category

        if "name" in updates and updates["name"] is not None:
            cleaned_name = updates["name"].strip()
            if not cleaned_name:
                raise DealFlowException("Category name cannot be empty", status_code=400)
            if cleaned_name.lower() != category.name.lower():
                existing = catalog_repository.get_category_by_name(db, cleaned_name)
                if existing and existing.id != category.id:
                    raise DealFlowException(
                        "A product category with this name already exists",
                        status_code=400,
                    )
            updates["name"] = cleaned_name

        if "description" in updates and updates["description"] is not None:
            updates["description"] = updates["description"].strip()

        return catalog_repository.update_category(db, category, updates)

    def deactivate_category(
        self, db: Session, category_id: uuid.UUID
    ) -> ProductCategory:
        """
        Deactivate a product category following the logical-deactivation convention.
        Validates existence and deactivates the record.
        """
        category = self.get_category_by_id(db, category_id)
        return catalog_repository.deactivate_category(db, category)

    # --- Product Operations ---

    def list_products(
        self,
        db: Session,
        search: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Product]:
        """List products with optional search, category, and active filters."""
        return catalog_repository.list_products(
            db=db,
            search=search,
            category_id=category_id,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

    def get_product_by_id(
        self, db: Session, product_id: uuid.UUID
    ) -> Product:
        """Fetch product by ID, ensuring existence."""
        product = catalog_repository.get_product_by_id(db, product_id)
        if not product:
            raise ResourceNotFoundError("Product not found")
        return product

    def create_product(
        self, db: Session, request: ProductCreateRequest
    ) -> Product:
        """
        Create a new product or service.
        Validates category existence and active status, SKU uniqueness, and persists the entity.
        """
        cleaned_name = request.name.strip()
        if not cleaned_name:
            raise DealFlowException("Product name cannot be empty", status_code=400)

        cleaned_sku = request.sku.strip().upper()
        if not cleaned_sku:
            raise DealFlowException("SKU cannot be empty", status_code=400)

        cleaned_unit = request.unit.strip()
        if not cleaned_unit:
            raise DealFlowException("Unit cannot be empty", status_code=400)

        # Validate category existence and active state
        category = catalog_repository.get_category_by_id(db, request.category_id)
        if not category:
            raise ResourceNotFoundError("Product category not found")
        if not category.is_active:
            raise DealFlowException(
                "Cannot assign an inactive product category", status_code=400
            )

        # Enforce unique SKU
        existing_sku = catalog_repository.get_product_by_sku(db, cleaned_sku)
        if existing_sku:
            raise DealFlowException(
                "A product with this SKU already exists", status_code=400
            )

        return catalog_repository.create_product(
            db=db,
            category_id=request.category_id,
            name=cleaned_name,
            sku=cleaned_sku,
            unit=cleaned_unit,
            base_price=request.base_price,
            cost_price=request.cost_price,
            tax_rate=request.tax_rate,
            description=request.description,
            is_subscription=request.is_subscription,
            is_active=request.is_active,
        )

    def update_product(
        self,
        db: Session,
        product_id: uuid.UUID,
        request: ProductUpdateRequest,
    ) -> Product:
        """
        Update an existing product.
        Validates existence, category existence (if changed), and SKU uniqueness (if changed).
        """
        product = self.get_product_by_id(db, product_id)

        updates = request.model_dump(exclude_unset=True)
        if not updates:
            return product

        if "category_id" in updates and updates["category_id"] is not None:
            category = catalog_repository.get_category_by_id(
                db, updates["category_id"]
            )
            if not category:
                raise ResourceNotFoundError("Product category not found")
            if not category.is_active:
                raise DealFlowException(
                    "Cannot assign an inactive product category", status_code=400
                )

        if "sku" in updates and updates["sku"] is not None:
            cleaned_sku = updates["sku"].strip().upper()
            if not cleaned_sku:
                raise DealFlowException("SKU cannot be empty", status_code=400)
            if cleaned_sku.lower() != product.sku.lower():
                existing = catalog_repository.get_product_by_sku(db, cleaned_sku)
                if existing and existing.id != product.id:
                    raise DealFlowException(
                        "A product with this SKU already exists",
                        status_code=400,
                    )
            updates["sku"] = cleaned_sku

        if "name" in updates and updates["name"] is not None:
            cleaned_name = updates["name"].strip()
            if not cleaned_name:
                raise DealFlowException(
                    "Product name cannot be empty", status_code=400
                )
            updates["name"] = cleaned_name

        if "unit" in updates and updates["unit"] is not None:
            cleaned_unit = updates["unit"].strip()
            if not cleaned_unit:
                raise DealFlowException(
                    "Unit cannot be empty", status_code=400
                )
            updates["unit"] = cleaned_unit

        if "description" in updates and updates["description"] is not None:
            updates["description"] = updates["description"].strip()

        return catalog_repository.update_product(db, product, updates)

    def deactivate_product(
        self, db: Session, product_id: uuid.UUID
    ) -> Product:
        """
        Deactivate a product following the logical-deactivation convention.
        Validates existence and sets is_active to False.
        """
        product = self.get_product_by_id(db, product_id)
        return catalog_repository.deactivate_product(db, product)

    # --- Product Variant Operations ---

    def list_variants_for_product(
        self,
        db: Session,
        product_id: uuid.UUID,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ProductVariant]:
        """
        List variants belonging to a specific product.
        Validates parent product existence.
        """
        # Ensure parent product exists
        self.get_product_by_id(db, product_id)
        return catalog_repository.list_variants_for_product(
            db=db,
            product_id=product_id,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

    def get_variant_by_id(
        self, db: Session, variant_id: uuid.UUID
    ) -> ProductVariant:
        """Fetch product variant by ID, ensuring existence."""
        variant = catalog_repository.get_variant_by_id(db, variant_id)
        if not variant:
            raise ResourceNotFoundError("Product variant not found")
        return variant

    def create_variant(
        self,
        db: Session,
        product_id: uuid.UUID,
        request: ProductVariantCreateRequest,
    ) -> ProductVariant:
        """
        Create a new product variant for a parent product.
        Validates parent product existence and active status.
        """
        product = self.get_product_by_id(db, product_id)
        if not product.is_active:
            raise DealFlowException(
                "Cannot create variant for an inactive product", status_code=400
            )

        cleaned_attr_name = request.attribute_name.strip()
        if not cleaned_attr_name:
            raise DealFlowException(
                "Attribute name cannot be empty", status_code=400
            )

        cleaned_attr_value = request.attribute_value.strip()
        if not cleaned_attr_value:
            raise DealFlowException(
                "Attribute value cannot be empty", status_code=400
            )

        cleaned_sku = request.sku.strip().upper() if request.sku else None

        return catalog_repository.create_variant(
            db=db,
            product_id=product_id,
            attribute_name=cleaned_attr_name,
            attribute_value=cleaned_attr_value,
            extra_price=request.extra_price,
            sku=cleaned_sku,
            is_active=request.is_active,
        )

    def update_variant(
        self,
        db: Session,
        variant_id: uuid.UUID,
        request: ProductVariantUpdateRequest,
    ) -> ProductVariant:
        """
        Update an existing product variant.
        Validates variant existence and applies updates.
        """
        variant = self.get_variant_by_id(db, variant_id)

        updates = request.model_dump(exclude_unset=True)
        if not updates:
            return variant

        if "attribute_name" in updates and updates["attribute_name"] is not None:
            cleaned_name = updates["attribute_name"].strip()
            if not cleaned_name:
                raise DealFlowException(
                    "Attribute name cannot be empty", status_code=400
                )
            updates["attribute_name"] = cleaned_name

        if "attribute_value" in updates and updates["attribute_value"] is not None:
            cleaned_val = updates["attribute_value"].strip()
            if not cleaned_val:
                raise DealFlowException(
                    "Attribute value cannot be empty", status_code=400
                )
            updates["attribute_value"] = cleaned_val

        if "sku" in updates and updates["sku"] is not None:
            cleaned_sku = updates["sku"].strip().upper()
            updates["sku"] = cleaned_sku if cleaned_sku else None

        return catalog_repository.update_variant(db, variant, updates)

    def deactivate_variant(
        self, db: Session, variant_id: uuid.UUID
    ) -> ProductVariant:
        """
        Deactivate a product variant following logical-deactivation convention.
        Validates existence and sets is_active to False.
        """
        variant = self.get_variant_by_id(db, variant_id)
        return catalog_repository.deactivate_variant(db, variant)


catalog_service = CatalogService()
ProductCategoryService = CatalogService
ProductVariantService = CatalogService
