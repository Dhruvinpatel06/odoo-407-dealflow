"""Discount Rules repository layer."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer_tier import CustomerTier
from app.models.discount_rule import DiscountRule
from app.models.product_category import ProductCategory


class DiscountRepository:
    """Encapsulates persistence operations for discount rules."""

    def get_discount_rule_by_id(
        self, db: Session, rule_id: uuid.UUID
    ) -> Optional[DiscountRule]:
        """Fetch discount rule by primary key."""
        return db.get(DiscountRule, rule_id)

    def list_discount_rules(
        self,
        db: Session,
        customer_tier_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DiscountRule]:
        """List discount rules with optional customer tier, category, and active filters."""
        stmt = select(DiscountRule)

        if customer_tier_id is not None:
            stmt = stmt.where(DiscountRule.customer_tier_id == customer_tier_id)

        if category_id is not None:
            stmt = stmt.where(DiscountRule.category_id == category_id)

        if is_active is not None:
            stmt = stmt.where(DiscountRule.is_active == is_active)

        stmt = (
            stmt.order_by(DiscountRule.priority.desc(), DiscountRule.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def create_discount_rule(
        self,
        db: Session,
        customer_tier_id: Optional[uuid.UUID],
        category_id: Optional[uuid.UUID],
        max_discount_percent: Decimal,
        priority: int = 0,
        is_active: bool = True,
    ) -> DiscountRule:
        """Create and persist a new discount rule."""
        rule = DiscountRule(
            customer_tier_id=customer_tier_id,
            category_id=category_id,
            max_discount_percent=max_discount_percent,
            priority=priority,
            is_active=is_active,
        )
        db.add(rule)
        db.flush()
        return rule

    def update_discount_rule(
        self,
        db: Session,
        rule: DiscountRule,
        updates: Dict[str, Any],
    ) -> DiscountRule:
        """Update fields of an existing discount rule."""
        for key, value in updates.items():
            setattr(rule, key, value)
        db.flush()
        return rule

    def deactivate_discount_rule(
        self, db: Session, rule: DiscountRule
    ) -> DiscountRule:
        """Logically deactivate a discount rule (preserves row for audit/history)."""
        rule.is_active = False
        db.flush()
        return rule

    def get_customer_tier(
        self, db: Session, tier_id: uuid.UUID
    ) -> Optional[CustomerTier]:
        """Fetch customer tier by primary key."""
        return db.get(CustomerTier, tier_id)

    def get_product_category(
        self, db: Session, category_id: uuid.UUID
    ) -> Optional[ProductCategory]:
        """Fetch product category by primary key."""
        return db.get(ProductCategory, category_id)

    def find_active_rules_by_conditions(
        self,
        db: Session,
        customer_tier_id: Optional[uuid.UUID],
        category_id: Optional[uuid.UUID],
    ) -> List[DiscountRule]:
        """Find active rules matching the specified tier and category conditions."""
        stmt = select(DiscountRule).where(
            DiscountRule.customer_tier_id == customer_tier_id,
            DiscountRule.category_id == category_id,
            DiscountRule.is_active.is_(True),
        )
        return list(db.scalars(stmt).all())

    def get_applicable_rules(
        self,
        db: Session,
        customer_tier_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
    ) -> List[DiscountRule]:
        """
        Fetch active discount rules applicable to the given customer tier and/or product category.
        Finds rules matching customer_tier_id (tier rules), category_id (category rules),
        or both (joint rules).
        """
        if customer_tier_id is None and category_id is None:
            return []

        from sqlalchemy import or_

        conditions = []
        if customer_tier_id is not None:
            conditions.append(DiscountRule.customer_tier_id == customer_tier_id)
        if category_id is not None:
            conditions.append(DiscountRule.category_id == category_id)

        stmt = (
            select(DiscountRule)
            .where(
                DiscountRule.is_active.is_(True),
                or_(*conditions),
            )
            .order_by(DiscountRule.priority.desc(), DiscountRule.max_discount_percent.asc())
        )
        return list(db.scalars(stmt).all())


discount_repository = DiscountRepository()
