"""Catalog repository layer."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.discount_rule import DiscountRule
from app.models.inventory import Inventory
from app.models.price_list_item import PriceListItem
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_variant import ProductVariant
from app.models.quotation_line import QuotationLine
from app.models.subscription import Subscription


class CatalogRepository:
    """Encapsulates persistence operations for catalog entities."""

    # --- Product Category Persistence ---

    def get_category_by_id(
        self, db: Session, category_id: uuid.UUID
    ) -> Optional[ProductCategory]:
        """Fetch product category by primary key."""
        return db.get(ProductCategory, category_id)

    def get_category_by_name(
        self, db: Session, name: str
    ) -> Optional[ProductCategory]:
        """Fetch product category by name (case-insensitive)."""
        stmt = select(ProductCategory).where(
            func.lower(ProductCategory.name) == name.strip().lower()
        )
        return db.scalars(stmt).first()

    def list_categories(
        self,
        db: Session,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ProductCategory]:
        """List product categories with optional active status filtering."""
        stmt = select(ProductCategory)
        if is_active is not None:
            stmt = stmt.where(ProductCategory.is_active == is_active)
        stmt = stmt.order_by(ProductCategory.name).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def create_category(
        self,
        db: Session,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> ProductCategory:
        """Create and persist a new product category."""
        category = ProductCategory(
            name=name.strip(),
            description=description.strip() if description else None,
            is_active=is_active,
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    def update_category(
        self,
        db: Session,
        category: ProductCategory,
        updates: Dict[str, Any],
    ) -> ProductCategory:
        """Update fields of an existing product category."""
        for key, value in updates.items():
            setattr(category, key, value)
        db.commit()
        db.refresh(category)
        return category

    def deactivate_category(
        self, db: Session, category: ProductCategory
    ) -> ProductCategory:
        """Logically deactivate a product category by setting is_active to False."""
        category.is_active = False
        db.commit()
        db.refresh(category)
        return category

    def delete_category(self, db: Session, category: ProductCategory) -> None:
        """Physically delete a product category."""
        db.delete(category)
        db.commit()

    def is_category_referenced(self, db: Session, category_id: uuid.UUID) -> bool:
        """Check whether a product category is referenced by products or discount rules."""
        has_products = (
            db.scalars(
                select(Product.id)
                .where(Product.category_id == category_id)
                .limit(1)
            ).first()
            is not None
        )
        if has_products:
            return True

        has_discount_rules = (
            db.scalars(
                select(DiscountRule.id)
                .where(DiscountRule.category_id == category_id)
                .limit(1)
            ).first()
            is not None
        )
        if has_discount_rules:
            return True

        return False

    # --- Product Persistence ---

    def get_product_by_id(
        self, db: Session, product_id: uuid.UUID
    ) -> Optional[Product]:
        """Fetch product by primary key with category relationship joined."""
        stmt = (
            select(Product)
            .options(joinedload(Product.category))
            .where(Product.id == product_id)
        )
        return db.scalars(stmt).first()

    def get_product_by_sku(
        self, db: Session, sku: str
    ) -> Optional[Product]:
        """Fetch product by SKU (case-insensitive)."""
        stmt = select(Product).where(
            func.lower(Product.sku) == sku.strip().lower()
        )
        return db.scalars(stmt).first()

    def list_products(
        self,
        db: Session,
        search: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Product]:
        """List products with optional search, category, and active status filters."""
        stmt = select(Product).options(joinedload(Product.category))

        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)

        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)

        if search:
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Product.name.ilike(search_pattern),
                    Product.sku.ilike(search_pattern),
                )
            )

        stmt = stmt.order_by(Product.name).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def create_product(
        self,
        db: Session,
        category_id: uuid.UUID,
        name: str,
        sku: str,
        unit: str,
        base_price: Decimal,
        cost_price: Decimal,
        tax_rate: Decimal,
        description: Optional[str] = None,
        is_subscription: bool = False,
        is_active: bool = True,
    ) -> Product:
        """Create and persist a new product."""
        product = Product(
            category_id=category_id,
            name=name.strip(),
            sku=sku.strip().upper(),
            unit=unit.strip(),
            base_price=base_price,
            cost_price=cost_price,
            tax_rate=tax_rate,
            description=description.strip() if description else None,
            is_subscription=is_subscription,
            is_active=is_active,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    def update_product(
        self,
        db: Session,
        product: Product,
        updates: Dict[str, Any],
    ) -> Product:
        """Update fields of an existing product."""
        for key, value in updates.items():
            setattr(product, key, value)
        db.commit()
        db.refresh(product)
        return product

    def deactivate_product(
        self, db: Session, product: Product
    ) -> Product:
        """Logically deactivate a product by setting is_active to False."""
        product.is_active = False
        db.commit()
        db.refresh(product)
        return product

    def is_product_referenced(self, db: Session, product_id: uuid.UUID) -> bool:
        """Check whether a product is referenced by variants, quotes, price lists, or subscriptions."""
        has_variants = (
            db.scalars(
                select(ProductVariant.id)
                .where(ProductVariant.product_id == product_id)
                .limit(1)
            ).first()
            is not None
        )
        if has_variants:
            return True

        has_quotation_lines = (
            db.scalars(
                select(QuotationLine.id)
                .where(QuotationLine.product_id == product_id)
                .limit(1)
            ).first()
            is not None
        )
        if has_quotation_lines:
            return True

        has_price_list_items = (
            db.scalars(
                select(PriceListItem.id)
                .where(PriceListItem.product_id == product_id)
                .limit(1)
            ).first()
            is not None
        )
        if has_price_list_items:
            return True

        has_inventory = (
            db.scalars(
                select(Inventory.id)
                .where(Inventory.product_id == product_id)
                .limit(1)
            ).first()
            is not None
        )
        if has_inventory:
            return True

        has_subscriptions = (
            db.scalars(
                select(Subscription.id)
                .where(Subscription.product_id == product_id)
                .limit(1)
            ).first()
            is not None
        )
        if has_subscriptions:
            return True

        return False

    # --- Product Variant Persistence ---

    def get_variant_by_id(
        self, db: Session, variant_id: uuid.UUID
    ) -> Optional[ProductVariant]:
        """Fetch product variant by primary key."""
        return db.get(ProductVariant, variant_id)

    def get_variant_by_sku(
        self, db: Session, sku: str
    ) -> Optional[ProductVariant]:
        """Fetch product variant by SKU (case-insensitive)."""
        stmt = select(ProductVariant).where(
            func.lower(ProductVariant.sku) == sku.strip().lower()
        )
        return db.scalars(stmt).first()

    def list_variants_for_product(
        self,
        db: Session,
        product_id: uuid.UUID,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ProductVariant]:
        """List product variants for a given product with optional active status filter."""
        stmt = select(ProductVariant).where(ProductVariant.product_id == product_id)
        if is_active is not None:
            stmt = stmt.where(ProductVariant.is_active == is_active)
        stmt = (
            stmt.order_by(ProductVariant.attribute_name, ProductVariant.attribute_value)
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def create_variant(
        self,
        db: Session,
        product_id: uuid.UUID,
        attribute_name: str,
        attribute_value: str,
        extra_price: Decimal,
        sku: Optional[str] = None,
        is_active: bool = True,
    ) -> ProductVariant:
        """Create and persist a new product variant."""
        variant = ProductVariant(
            product_id=product_id,
            attribute_name=attribute_name.strip(),
            attribute_value=attribute_value.strip(),
            extra_price=extra_price,
            sku=sku.strip().upper() if sku else None,
            is_active=is_active,
        )
        db.add(variant)
        db.commit()
        db.refresh(variant)
        return variant

    def update_variant(
        self,
        db: Session,
        variant: ProductVariant,
        updates: Dict[str, Any],
    ) -> ProductVariant:
        """Update fields of an existing product variant."""
        for key, value in updates.items():
            setattr(variant, key, value)
        db.commit()
        db.refresh(variant)
        return variant

    def deactivate_variant(
        self, db: Session, variant: ProductVariant
    ) -> ProductVariant:
        """Logically deactivate a product variant by setting is_active to False."""
        variant.is_active = False
        db.commit()
        db.refresh(variant)
        return variant

    def is_variant_referenced(self, db: Session, variant_id: uuid.UUID) -> bool:
        """Check whether a product variant is referenced by quotation lines or price list items."""
        has_quotation_lines = (
            db.scalars(
                select(QuotationLine.id)
                .where(QuotationLine.variant_id == variant_id)
                .limit(1)
            ).first()
            is not None
        )
        if has_quotation_lines:
            return True

        has_price_list_items = (
            db.scalars(
                select(PriceListItem.id)
                .where(PriceListItem.variant_id == variant_id)
                .limit(1)
            ).first()
            is not None
        )
        if has_price_list_items:
            return True

        return False


catalog_repository = CatalogRepository()
ProductCategoryRepository = CatalogRepository
ProductVariantRepository = CatalogRepository
