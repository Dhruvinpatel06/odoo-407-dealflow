"""Pricing service layer."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import DealFlowException, ResourceNotFoundError
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.price_list import PriceList
from app.models.price_list_item import PriceListItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.modules.pricing.engine import pricing_engine
from app.modules.pricing.repository import pricing_repository
from app.modules.pricing.schemas import (
    PriceListCreateRequest,
    PriceListItemCreateRequest,
    PriceListItemUpdateRequest,
    PriceListUpdateRequest,
    PricingResolveRequest,
    PricingResolveResponse,
)


class PricingService:
    """Coordinates business logic and workflows for pricing and price lists."""

    def get_price_list_by_id(
        self, db: Session, price_list_id: uuid.UUID
    ) -> PriceList:
        """Fetch price list by UUID, ensuring existence."""
        price_list = pricing_repository.get_price_list_by_id(db, price_list_id)
        if not price_list:
            raise ResourceNotFoundError("Price list not found")
        return price_list

    def list_price_lists(
        self,
        db: Session,
        customer_tier_id: Optional[uuid.UUID] = None,
        currency: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PriceList]:
        """List price lists with optional filters."""
        return pricing_repository.list_price_lists(
            db=db,
            customer_tier_id=customer_tier_id,
            currency=currency,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

    def create_price_list(
        self, db: Session, request: PriceListCreateRequest
    ) -> PriceList:
        """Create a new price list with uniqueness and tier validation."""
        cleaned_name = request.name.strip()
        if not cleaned_name:
            raise DealFlowException("Price list name cannot be empty", status_code=400)

        existing = pricing_repository.get_price_list_by_name(db, cleaned_name)
        if existing:
            raise DealFlowException(
                "A price list with this name already exists", status_code=400
            )

        cleaned_currency = request.currency.strip().upper()
        if len(cleaned_currency) != 3 or not cleaned_currency.isalpha():
            raise DealFlowException("Currency must be a 3-letter ISO code", status_code=400)

        if request.customer_tier_id is not None:
            tier = db.get(CustomerTier, request.customer_tier_id)
            if not tier:
                raise ResourceNotFoundError("Customer tier not found")
            if not tier.is_active:
                raise DealFlowException("Customer tier is inactive", status_code=400)

        return pricing_repository.create_price_list(
            db=db,
            name=cleaned_name,
            currency=cleaned_currency,
            customer_tier_id=request.customer_tier_id,
            is_active=request.is_active,
        )

    def update_price_list(
        self,
        db: Session,
        price_list_id: uuid.UUID,
        request: PriceListUpdateRequest,
    ) -> PriceList:
        """Update an existing price list."""
        price_list = self.get_price_list_by_id(db, price_list_id)
        updates = request.model_dump(exclude_unset=True)
        if not updates:
            return price_list

        if "name" in updates and updates["name"] is not None:
            cleaned_name = updates["name"].strip()
            if not cleaned_name:
                raise DealFlowException("Price list name cannot be empty", status_code=400)
            if cleaned_name.lower() != price_list.name.lower():
                existing = pricing_repository.get_price_list_by_name(db, cleaned_name)
                if existing and existing.id != price_list.id:
                    raise DealFlowException(
                        "A price list with this name already exists", status_code=400
                    )
            updates["name"] = cleaned_name

        if "currency" in updates and updates["currency"] is not None:
            cleaned_currency = updates["currency"].strip().upper()
            if len(cleaned_currency) != 3 or not cleaned_currency.isalpha():
                raise DealFlowException("Currency must be a 3-letter ISO code", status_code=400)
            updates["currency"] = cleaned_currency

        if "customer_tier_id" in updates:
            tier_id = updates["customer_tier_id"]
            if tier_id is not None:
                tier = db.get(CustomerTier, tier_id)
                if not tier:
                    raise ResourceNotFoundError("Customer tier not found")
                if not tier.is_active:
                    raise DealFlowException("Customer tier is inactive", status_code=400)

        return pricing_repository.update_price_list(db, price_list, updates)

    def deactivate_price_list(
        self, db: Session, price_list_id: uuid.UUID
    ) -> PriceList:
        """Logically deactivate a price list (record is preserved)."""
        price_list = self.get_price_list_by_id(db, price_list_id)
        return pricing_repository.deactivate_price_list(db, price_list)

    # --- Price List Items ---

    def list_items_for_price_list(
        self, db: Session, price_list_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[PriceListItem]:
        """List items belonging to a price list after verifying parent exists."""
        self.get_price_list_by_id(db, price_list_id)
        return pricing_repository.list_items_for_price_list(
            db=db, price_list_id=price_list_id, skip=skip, limit=limit
        )

    def create_price_list_item(
        self,
        db: Session,
        price_list_id: uuid.UUID,
        request: PriceListItemCreateRequest,
    ) -> PriceListItem:
        """Add an item price override to a price list with full validation."""
        self.get_price_list_by_id(db, price_list_id)

        if request.price < Decimal("0.00"):
            raise DealFlowException("Price cannot be negative", status_code=400)

        product = db.get(Product, request.product_id)
        if not product:
            raise ResourceNotFoundError("Product not found")
        if not product.is_active:
            raise DealFlowException("Product is inactive", status_code=400)

        if request.variant_id is not None:
            variant = db.get(ProductVariant, request.variant_id)
            if not variant:
                raise ResourceNotFoundError("Product variant not found")
            if variant.product_id != product.id:
                raise DealFlowException(
                    "Variant does not belong to the specified product",
                    status_code=400,
                )
            if not variant.is_active:
                raise DealFlowException("Product variant is inactive", status_code=400)

        existing = pricing_repository.get_item_by_product_variant(
            db=db,
            price_list_id=price_list_id,
            product_id=request.product_id,
            variant_id=request.variant_id,
        )
        if existing:
            raise DealFlowException(
                "A price list item for this product/variant already exists",
                status_code=400,
            )

        return pricing_repository.create_price_list_item(
            db=db,
            price_list_id=price_list_id,
            product_id=request.product_id,
            price=request.price,
            variant_id=request.variant_id,
        )

    def update_price_list_item(
        self,
        db: Session,
        price_list_id: uuid.UUID,
        item_id: uuid.UUID,
        request: PriceListItemUpdateRequest,
    ) -> PriceListItem:
        """Update an item in a price list with full validation."""
        self.get_price_list_by_id(db, price_list_id)
        item = pricing_repository.get_price_list_item_by_id(db, item_id)
        if not item or item.price_list_id != price_list_id:
            raise ResourceNotFoundError("Price list item not found")

        updates = request.model_dump(exclude_unset=True)
        if not updates:
            return item

        if "price" in updates and updates["price"] is not None:
            if updates["price"] < Decimal("0.00"):
                raise DealFlowException("Price cannot be negative", status_code=400)

        if "variant_id" in updates:
            new_variant_id = updates["variant_id"]
            if new_variant_id is not None:
                variant = db.get(ProductVariant, new_variant_id)
                if not variant:
                    raise ResourceNotFoundError("Product variant not found")
                if variant.product_id != item.product_id:
                    raise DealFlowException(
                        "Variant does not belong to the product", status_code=400
                    )
                if not variant.is_active:
                    raise DealFlowException(
                        "Product variant is inactive", status_code=400
                    )

            # Check if this variant change creates a duplicate item in the price list
            duplicate = pricing_repository.get_item_by_product_variant(
                db=db,
                price_list_id=price_list_id,
                product_id=item.product_id,
                variant_id=new_variant_id,
            )
            if duplicate and duplicate.id != item.id:
                raise DealFlowException(
                    "A price list item for this product/variant already exists",
                    status_code=400,
                )

        return pricing_repository.update_price_list_item(db, item, updates)

    def delete_price_list_item(
        self, db: Session, price_list_id: uuid.UUID, item_id: uuid.UUID
    ) -> None:
        """Remove a price list item after validating parent and existence."""
        self.get_price_list_by_id(db, price_list_id)
        item = pricing_repository.get_price_list_item_by_id(db, item_id)
        if not item or item.price_list_id != price_list_id:
            raise ResourceNotFoundError("Price list item not found")
        pricing_repository.delete_price_list_item(db, item)

    # --- Authoritative Pricing Resolution ---

    def resolve_price(
        self, db: Session, request: PricingResolveRequest
    ) -> PricingResolveResponse:
        """
        Determine the authoritative selling price for a product/variant in the
        context of customer, tier, currency, and price list.
        Never trusts client-supplied prices.
        """
        product = db.get(Product, request.product_id)
        if not product:
            raise ResourceNotFoundError("Product not found")
        if not product.is_active:
            raise DealFlowException("Product is inactive", status_code=400)

        variant = None
        variant_extra = Decimal("0.00")
        if request.variant_id is not None:
            variant = db.get(ProductVariant, request.variant_id)
            if not variant:
                raise ResourceNotFoundError("Product variant not found")
            if variant.product_id != product.id:
                raise DealFlowException(
                    "Variant does not belong to the specified product",
                    status_code=400,
                )
            if not variant.is_active:
                raise DealFlowException("Product variant is inactive", status_code=400)
            variant_extra = variant.extra_price

        currency = request.currency.strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise DealFlowException("Currency must be a 3-letter ISO code", status_code=400)

        # Resolve customer tier context
        effective_tier_id: Optional[uuid.UUID] = None
        if request.customer_tier_id is not None:
            tier = db.get(CustomerTier, request.customer_tier_id)
            if not tier:
                raise ResourceNotFoundError("Customer tier not found")
            if not tier.is_active:
                raise DealFlowException("Customer tier is inactive", status_code=400)
            effective_tier_id = tier.id

        if request.customer_id is not None:
            customer = db.get(Customer, request.customer_id)
            if not customer:
                raise ResourceNotFoundError("Customer not found")
            if not customer.is_active:
                raise DealFlowException("Customer is inactive", status_code=400)
            if effective_tier_id is None:
                effective_tier_id = customer.customer_tier_id

        # Case 1: Explicit Price List specified
        if request.price_list_id is not None:
            price_list = db.get(PriceList, request.price_list_id)
            if not price_list:
                raise ResourceNotFoundError("Price list not found")
            if not price_list.is_active:
                raise DealFlowException("Price list is inactive", status_code=400)
            if price_list.currency != currency:
                raise DealFlowException(
                    f"Price list currency '{price_list.currency}' does not match requested currency '{currency}'",
                    status_code=400,
                )
            if (
                price_list.customer_tier_id is not None
                and effective_tier_id is not None
                and price_list.customer_tier_id != effective_tier_id
            ):
                raise DealFlowException(
                    "Specified price list does not belong to customer tier",
                    status_code=400,
                )

            item = pricing_repository.find_price_list_item(
                db=db,
                price_list_id=price_list.id,
                product_id=product.id,
                variant_id=request.variant_id,
            )
            if not item:
                raise ResourceNotFoundError(
                    "No applicable price-list item found in specified price list"
                )

            is_variant_override = item.variant_id is not None
            resolved_price, effective_extra = pricing_engine.calculate_resolved_price(
                base_unit_price=item.price,
                variant_extra_price=variant_extra,
                is_variant_specific_override=is_variant_override,
            )
            return PricingResolveResponse(
                product_id=product.id,
                variant_id=request.variant_id,
                price_list_id=price_list.id,
                currency=currency,
                base_price=item.price,
                variant_extra_price=effective_extra,
                resolved_unit_price=resolved_price,
                cost_price=product.cost_price,
                pricing_source="PRICE_LIST",
            )

        # Case 2: Automatic resolution (Tier-specific price list -> General price list -> Base catalog)
        applicable_pl = None
        item = None

        # 2a. Check tier-specific price list if tier context exists
        if effective_tier_id is not None:
            tier_pl = pricing_repository.find_applicable_price_list(
                db=db,
                currency=currency,
                customer_tier_id=effective_tier_id,
            )
            if tier_pl and tier_pl.customer_tier_id == effective_tier_id:
                tier_item = pricing_repository.find_price_list_item(
                    db=db,
                    price_list_id=tier_pl.id,
                    product_id=product.id,
                    variant_id=request.variant_id,
                )
                if tier_item:
                    applicable_pl = tier_pl
                    item = tier_item

        # 2b. Check general active price list (customer_tier_id is None)
        if not applicable_pl:
            gen_pl = pricing_repository.find_applicable_price_list(
                db=db,
                currency=currency,
                customer_tier_id=None,
            )
            if gen_pl:
                gen_item = pricing_repository.find_price_list_item(
                    db=db,
                    price_list_id=gen_pl.id,
                    product_id=product.id,
                    variant_id=request.variant_id,
                )
                if gen_item:
                    applicable_pl = gen_pl
                    item = gen_item

        # If a price list item override was located
        if applicable_pl and item:
            is_variant_override = item.variant_id is not None
            resolved_price, effective_extra = pricing_engine.calculate_resolved_price(
                base_unit_price=item.price,
                variant_extra_price=variant_extra,
                is_variant_specific_override=is_variant_override,
            )
            return PricingResolveResponse(
                product_id=product.id,
                variant_id=request.variant_id,
                price_list_id=applicable_pl.id,
                currency=currency,
                base_price=item.price,
                variant_extra_price=effective_extra,
                resolved_unit_price=resolved_price,
                cost_price=product.cost_price,
                pricing_source="PRICE_LIST",
            )

        # 2c. Fallback to base catalog
        resolved_price, effective_extra = pricing_engine.calculate_resolved_price(
            base_unit_price=product.base_price,
            variant_extra_price=variant_extra,
            is_variant_specific_override=False,
        )
        return PricingResolveResponse(
            product_id=product.id,
            variant_id=request.variant_id,
            price_list_id=None,
            currency=currency,
            base_price=product.base_price,
            variant_extra_price=effective_extra,
            resolved_unit_price=resolved_price,
            cost_price=product.cost_price,
            pricing_source="BASE_CATALOG",
        )


pricing_service = PricingService()
