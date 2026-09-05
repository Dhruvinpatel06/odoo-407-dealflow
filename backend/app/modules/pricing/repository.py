"""Pricing repository layer."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.price_list import PriceList
from app.models.price_list_item import PriceListItem


class PricingRepository:
    """Encapsulates persistence operations for price lists and price list items."""

    # --- Price List Operations ---

    def get_price_list_by_id(
        self, db: Session, price_list_id: uuid.UUID
    ) -> Optional[PriceList]:
        """Fetch price list by primary key."""
        return db.get(PriceList, price_list_id)

    def get_price_list_by_name(
        self, db: Session, name: str
    ) -> Optional[PriceList]:
        """Fetch price list by name (case-insensitive)."""
        stmt = select(PriceList).where(
            func.lower(PriceList.name) == name.strip().lower()
        )
        return db.scalars(stmt).first()

    def list_price_lists(
        self,
        db: Session,
        customer_tier_id: Optional[uuid.UUID] = None,
        currency: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PriceList]:
        """List price lists with optional customer tier, currency, and active filters."""
        stmt = select(PriceList)

        if customer_tier_id is not None:
            stmt = stmt.where(PriceList.customer_tier_id == customer_tier_id)

        if currency is not None:
            stmt = stmt.where(PriceList.currency == currency.upper())

        if is_active is not None:
            stmt = stmt.where(PriceList.is_active == is_active)

        stmt = stmt.order_by(PriceList.name).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def create_price_list(
        self,
        db: Session,
        name: str,
        currency: str,
        customer_tier_id: Optional[uuid.UUID] = None,
        is_active: bool = True,
    ) -> PriceList:
        """Create and persist a new price list."""
        price_list = PriceList(
            name=name.strip(),
            currency=currency.strip().upper(),
            customer_tier_id=customer_tier_id,
            is_active=is_active,
        )
        db.add(price_list)
        db.commit()
        db.refresh(price_list)
        return price_list

    def update_price_list(
        self,
        db: Session,
        price_list: PriceList,
        updates: Dict[str, Any],
    ) -> PriceList:
        """Update fields of an existing price list."""
        for key, value in updates.items():
            setattr(price_list, key, value)
        db.commit()
        db.refresh(price_list)
        return price_list

    def deactivate_price_list(
        self, db: Session, price_list: PriceList
    ) -> PriceList:
        """Logically deactivate a price list."""
        price_list.is_active = False
        db.commit()
        db.refresh(price_list)
        return price_list

    # --- Price List Item Operations ---

    def get_price_list_item_by_id(
        self, db: Session, item_id: uuid.UUID
    ) -> Optional[PriceListItem]:
        """Fetch a price list item by primary key."""
        return db.get(PriceListItem, item_id)

    def list_items_for_price_list(
        self,
        db: Session,
        price_list_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PriceListItem]:
        """List items belonging to a price list."""
        stmt = (
            select(PriceListItem)
            .where(PriceListItem.price_list_id == price_list_id)
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def get_item_by_product_variant(
        self,
        db: Session,
        price_list_id: uuid.UUID,
        product_id: uuid.UUID,
        variant_id: Optional[uuid.UUID] = None,
    ) -> Optional[PriceListItem]:
        """Find a specific item in a price list by product and variant."""
        stmt = (
            select(PriceListItem)
            .where(PriceListItem.price_list_id == price_list_id)
            .where(PriceListItem.product_id == product_id)
        )
        if variant_id is not None:
            stmt = stmt.where(PriceListItem.variant_id == variant_id)
        else:
            stmt = stmt.where(PriceListItem.variant_id.is_(None))

        return db.scalars(stmt).first()

    def create_price_list_item(
        self,
        db: Session,
        price_list_id: uuid.UUID,
        product_id: uuid.UUID,
        price: Decimal,
        variant_id: Optional[uuid.UUID] = None,
    ) -> PriceListItem:
        """Create and persist a price list item."""
        item = PriceListItem(
            price_list_id=price_list_id,
            product_id=product_id,
            variant_id=variant_id,
            price=price,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def update_price_list_item(
        self,
        db: Session,
        item: PriceListItem,
        updates: Dict[str, Any],
    ) -> PriceListItem:
        """Update fields of an existing price list item."""
        for key, value in updates.items():
            setattr(item, key, value)
        db.commit()
        db.refresh(item)
        return item

    def delete_price_list_item(
        self, db: Session, item: PriceListItem
    ) -> None:
        """Delete a price list item."""
        db.delete(item)
        db.commit()

    # --- Pricing Resolution Query Helpers ---

    def find_applicable_price_list(
        self,
        db: Session,
        currency: str,
        customer_tier_id: Optional[uuid.UUID] = None,
    ) -> Optional[PriceList]:
        """
        Find an active price list matching tier and currency, or general active price list.
        Tier-specific price list takes precedence over general price list.
        """
        clean_currency = currency.strip().upper()
        if customer_tier_id is not None:
            stmt = (
                select(PriceList)
                .where(
                    PriceList.customer_tier_id == customer_tier_id,
                    PriceList.currency == clean_currency,
                    PriceList.is_active.is_(True),
                )
                .order_by(PriceList.created_at.desc())
            )
            pl = db.scalars(stmt).first()
            if pl:
                return pl

        # Fallback to general price list (tier is NULL)
        stmt = (
            select(PriceList)
            .where(
                PriceList.customer_tier_id.is_(None),
                PriceList.currency == clean_currency,
                PriceList.is_active.is_(True),
            )
            .order_by(PriceList.created_at.desc())
        )
        return db.scalars(stmt).first()

    def find_price_list_item(
        self,
        db: Session,
        price_list_id: uuid.UUID,
        product_id: uuid.UUID,
        variant_id: Optional[uuid.UUID] = None,
    ) -> Optional[PriceListItem]:
        """
        Find the best matching item in a price list for a product and optional variant.
        Checks for exact variant match first; falls back to product-level match (variant_id is NULL).
        """
        if variant_id is not None:
            stmt = select(PriceListItem).where(
                PriceListItem.price_list_id == price_list_id,
                PriceListItem.product_id == product_id,
                PriceListItem.variant_id == variant_id,
            )
            item = db.scalars(stmt).first()
            if item:
                return item

        # Check product-level override
        stmt = select(PriceListItem).where(
            PriceListItem.price_list_id == price_list_id,
            PriceListItem.product_id == product_id,
            PriceListItem.variant_id.is_(None),
        )
        return db.scalars(stmt).first()


pricing_repository = PricingRepository()
