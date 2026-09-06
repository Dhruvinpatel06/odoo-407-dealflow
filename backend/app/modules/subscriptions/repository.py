"""Subscriptions repository layer for database persistence."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.common.enums import SubscriptionStatus
from app.models.customer import Customer
from app.models.product import Product
from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan


class SubscriptionsRepository:
    """Handles persistence queries for Subscription Plans and Subscriptions."""

    # =====================================================================
    # Subscription Plans
    # =====================================================================

    def list_plans(
        self,
        db: Session,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SubscriptionPlan]:
        """List subscription plans with optional is_active filter."""
        stmt = select(SubscriptionPlan)
        if is_active is not None:
            stmt = stmt.where(SubscriptionPlan.is_active == is_active)
        stmt = stmt.order_by(SubscriptionPlan.name.asc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def get_plan_by_id(
        self, db: Session, plan_id: uuid.UUID
    ) -> Optional[SubscriptionPlan]:
        """Fetch plan by UUID."""
        return db.get(SubscriptionPlan, plan_id)

    def create_plan(
        self, db: Session, plan: SubscriptionPlan
    ) -> SubscriptionPlan:
        """Persist new subscription plan."""
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    def update_plan(
        self, db: Session, plan: SubscriptionPlan
    ) -> SubscriptionPlan:
        """Commit updates to a subscription plan."""
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    # =====================================================================
    # Subscriptions
    # =====================================================================

    def list_subscriptions(
        self,
        db: Session,
        customer_id: Optional[uuid.UUID] = None,
        status: Optional[SubscriptionStatus] = None,
        order_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Subscription]:
        """List subscriptions with optional filters and relations loaded."""
        stmt = (
            select(Subscription)
            .options(
                joinedload(Subscription.customer),
                joinedload(Subscription.product),
                joinedload(Subscription.plan),
            )
        )
        if customer_id is not None:
            stmt = stmt.where(Subscription.customer_id == customer_id)
        if status is not None:
            stmt = stmt.where(Subscription.status == status)
        if order_id is not None:
            stmt = stmt.where(Subscription.order_id == order_id)

        stmt = stmt.order_by(Subscription.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).unique().all())

    def get_subscription_by_id(
        self, db: Session, subscription_id: uuid.UUID
    ) -> Optional[Subscription]:
        """Fetch subscription by UUID with relations loaded."""
        stmt = (
            select(Subscription)
            .options(
                joinedload(Subscription.customer),
                joinedload(Subscription.product),
                joinedload(Subscription.plan),
                joinedload(Subscription.billing_schedules),
            )
            .where(Subscription.id == subscription_id)
        )
        return db.scalars(stmt).unique().first()

    def get_subscription_by_quotation_line_id(
        self, db: Session, quotation_line_id: uuid.UUID
    ) -> Optional[Subscription]:
        """Fetch subscription associated with a specific quotation line."""
        stmt = select(Subscription).where(
            Subscription.quotation_line_id == quotation_line_id
        )
        return db.scalars(stmt).first()

    def create_subscription(
        self, db: Session, subscription: Subscription
    ) -> Subscription:
        """Persist new subscription."""
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription

    def update_subscription(
        self, db: Session, subscription: Subscription
    ) -> Subscription:
        """Commit updates to an existing subscription."""
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription


subscriptions_repository = SubscriptionsRepository()
