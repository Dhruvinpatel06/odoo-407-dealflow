"""Customers repository layer."""

import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.discount_rule import DiscountRule
from app.models.negotiation_request import NegotiationRequest
from app.models.order import Order
from app.models.price_list import PriceList
from app.models.quotation import Quotation
from app.models.subscription import Subscription
from app.models.user import User


class CustomerRepository:
    """Encapsulates persistence operations for customer and customer tier entities."""

    def get_tier_by_id(
        self, db: Session, tier_id: uuid.UUID
    ) -> Optional[CustomerTier]:
        """Fetch customer tier by primary key."""
        return db.get(CustomerTier, tier_id)

    def get_tier_by_name(
        self, db: Session, name: str
    ) -> Optional[CustomerTier]:
        """Fetch customer tier by name (case-insensitive)."""
        stmt = select(CustomerTier).where(
            func.lower(CustomerTier.name) == name.strip().lower()
        )
        return db.scalars(stmt).first()

    def list_tiers(
        self,
        db: Session,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CustomerTier]:
        """List customer tiers with optional active status filtering."""
        stmt = select(CustomerTier)
        if is_active is not None:
            stmt = stmt.where(CustomerTier.is_active == is_active)
        stmt = stmt.order_by(CustomerTier.name).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def create_tier(
        self,
        db: Session,
        name: str,
        default_discount_limit: Decimal,
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> CustomerTier:
        """Create and persist a new customer tier."""
        tier = CustomerTier(
            name=name.strip(),
            description=description.strip() if description else None,
            default_discount_limit=default_discount_limit,
            is_active=is_active,
        )
        db.add(tier)
        db.commit()
        db.refresh(tier)
        return tier

    def update_tier(
        self,
        db: Session,
        tier: CustomerTier,
        updates: Dict[str, Any],
    ) -> CustomerTier:
        """Update fields of an existing customer tier."""
        for key, value in updates.items():
            setattr(tier, key, value)
        db.commit()
        db.refresh(tier)
        return tier

    def deactivate_tier(
        self, db: Session, tier: CustomerTier
    ) -> CustomerTier:
        """Logically deactivate a customer tier by setting is_active to False."""
        tier.is_active = False
        db.commit()
        db.refresh(tier)
        return tier

    def is_tier_referenced(self, db: Session, tier_id: uuid.UUID) -> bool:
        """Check whether a customer tier is referenced by customers, discount rules, or price lists."""
        has_customers = (
            db.scalars(
                select(Customer.id)
                .where(Customer.customer_tier_id == tier_id)
                .limit(1)
            ).first()
            is not None
        )
        if has_customers:
            return True

        has_discount_rules = (
            db.scalars(
                select(DiscountRule.id)
                .where(DiscountRule.customer_tier_id == tier_id)
                .limit(1)
            ).first()
            is not None
        )
        if has_discount_rules:
            return True

        has_price_lists = (
            db.scalars(
                select(PriceList.id)
                .where(PriceList.customer_tier_id == tier_id)
                .limit(1)
            ).first()
            is not None
        )
        return has_price_lists

    def get_customer_by_id(
        self, db: Session, customer_id: uuid.UUID
    ) -> Optional[Customer]:
        """Fetch customer by primary key."""
        return db.get(Customer, customer_id)

    def get_customer_with_tier(
        self, db: Session, customer_id: uuid.UUID
    ) -> Optional[Customer]:
        """Fetch customer by primary key eagerly loading the associated customer tier."""
        stmt = (
            select(Customer)
            .options(joinedload(Customer.tier))
            .where(Customer.id == customer_id)
        )
        return db.scalars(stmt).first()

    def create_customer(
        self,
        db: Session,
        name: str,
        customer_tier_id: uuid.UUID,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        billing_address: Optional[str] = None,
        shipping_address: Optional[str] = None,
        is_active: bool = True,
    ) -> Customer:
        """Create and persist a new customer record."""
        customer = Customer(
            name=name.strip(),
            customer_tier_id=customer_tier_id,
            email=email.strip() if email else None,
            phone=phone.strip() if phone else None,
            billing_address=billing_address.strip() if billing_address else None,
            shipping_address=shipping_address.strip() if shipping_address else None,
            is_active=is_active,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    def update_customer(
        self,
        db: Session,
        customer: Customer,
        updates: Dict[str, Any],
    ) -> Customer:
        """Update fields of an existing customer record."""
        for key, value in updates.items():
            setattr(customer, key, value)
        db.commit()
        db.refresh(customer)
        return customer

    def deactivate_customer(
        self, db: Session, customer: Customer
    ) -> Customer:
        """Logically deactivate a customer by setting is_active to False."""
        customer.is_active = False
        db.commit()
        db.refresh(customer)
        return customer

    def delete_customer(
        self, db: Session, customer: Customer
    ) -> None:
        """Physically delete a customer record."""
        db.delete(customer)
        db.commit()

    def is_customer_referenced(
        self, db: Session, customer_id: uuid.UUID
    ) -> bool:
        """Check whether a customer has existing references in business records."""
        has_users = (
            db.scalars(
                select(User.id).where(User.customer_id == customer_id).limit(1)
            ).first()
            is not None
        )
        if has_users:
            return True

        has_quotations = (
            db.scalars(
                select(Quotation.id)
                .where(Quotation.customer_id == customer_id)
                .limit(1)
            ).first()
            is not None
        )
        if has_quotations:
            return True

        has_orders = (
            db.scalars(
                select(Order.id).where(Order.customer_id == customer_id).limit(1)
            ).first()
            is not None
        )
        if has_orders:
            return True

        has_subscriptions = (
            db.scalars(
                select(Subscription.id)
                .where(Subscription.customer_id == customer_id)
                .limit(1)
            ).first()
            is not None
        )
        if has_subscriptions:
            return True

        has_negotiation_requests = (
            db.scalars(
                select(NegotiationRequest.id)
                .where(NegotiationRequest.customer_id == customer_id)
                .limit(1)
            ).first()
            is not None
        )
        return has_negotiation_requests

    def list_customers(
        self,
        db: Session,
        search: Optional[str] = None,
        customer_tier_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Customer]:
        """List and search customers with optional filters and lifecycle state awareness."""
        stmt = select(Customer)

        if is_active is not None:
            stmt = stmt.where(Customer.is_active == is_active)

        if customer_tier_id is not None:
            stmt = stmt.where(Customer.customer_tier_id == customer_tier_id)

        if search:
            cleaned = search.strip()
            if cleaned:
                term = f"%{cleaned.lower()}%"
                stmt = stmt.where(
                    or_(
                        func.lower(Customer.name).like(term),
                        func.lower(Customer.email).like(term),
                        Customer.phone.like(f"%{cleaned}%"),
                    )
                )

        stmt = stmt.order_by(Customer.name).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def list_customer_quotations(
        self,
        db: Session,
        customer_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Quotation]:
        """Query quotations belonging to a customer, ordered by creation date descending."""
        stmt = (
            select(Quotation)
            .where(Quotation.customer_id == customer_id)
            .order_by(Quotation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def list_customer_orders(
        self,
        db: Session,
        customer_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Query orders belonging to a customer, ordered by confirmation date descending."""
        stmt = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(Order.confirmed_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def list_customer_subscriptions(
        self,
        db: Session,
        customer_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Subscription]:
        """Query subscriptions belonging to a customer, ordered by creation date descending."""
        stmt = (
            select(Subscription)
            .where(Subscription.customer_id == customer_id)
            .order_by(Subscription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def get_customer_by_email(
        self, db: Session, email: str
    ) -> Optional[Customer]:
        """Fetch customer record by email (case-insensitive)."""
        stmt = select(Customer).where(
            func.lower(Customer.email) == email.strip().lower()
        )
        return db.scalars(stmt).first()

    def get_customer_by_user_id(
        self, db: Session, user_id: uuid.UUID
    ) -> Optional[Customer]:
        """Fetch customer record linked to a user."""
        stmt = (
            select(Customer)
            .join(User, User.customer_id == Customer.id)
            .where(User.id == user_id)
        )
        return db.scalars(stmt).first()

    def get_default_tier(self, db: Session) -> CustomerTier:
        """Fetch or create default active customer tier."""
        for name in ["STANDARD", "DEFAULT", "BRONZE", "GOLD"]:
            tier = db.scalars(
                select(CustomerTier).where(
                    func.upper(CustomerTier.name) == name,
                    CustomerTier.is_active.is_(True),
                )
            ).first()
            if tier:
                return tier

        tier = db.scalars(
            select(CustomerTier)
            .where(CustomerTier.is_active.is_(True))
            .order_by(CustomerTier.default_discount_limit.asc())
        ).first()
        if tier:
            return tier

        tier = CustomerTier(
            name="STANDARD",
            description="Default Customer Tier",
            default_discount_limit=Decimal("0.00"),
            is_active=True,
        )
        db.add(tier)
        db.flush()
        return tier


customer_repository = CustomerRepository()
