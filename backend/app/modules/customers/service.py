"""Customers service layer."""

import uuid
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.exceptions import DealFlowException, ResourceNotFoundError
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.order import Order
from app.models.quotation import Quotation
from app.models.subscription import Subscription
from app.models.user import User
from app.modules.customers.repository import customer_repository
from app.modules.customers.schemas import (
    CustomerCreate,
    CustomerTierCreateRequest,
    CustomerTierUpdateRequest,
    CustomerUpdate,
)


class CustomerService:
    """Coordinates business logic and workflows for customers and customer tiers."""

    def list_tiers(
        self,
        db: Session,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CustomerTier]:
        """List customer tiers with optional active status filtering."""
        return customer_repository.list_tiers(
            db=db, is_active=is_active, skip=skip, limit=limit
        )

    def get_tier_by_id(self, db: Session, tier_id: uuid.UUID) -> CustomerTier:
        """Fetch customer tier by id, ensuring existence."""
        tier = customer_repository.get_tier_by_id(db, tier_id)
        if not tier:
            raise ResourceNotFoundError("Customer tier not found")
        return tier

    def create_tier(
        self, db: Session, request: CustomerTierCreateRequest
    ) -> CustomerTier:
        """
        Create a new customer tier.
        Validates tier name uniqueness and persists the tier.
        """
        cleaned_name = request.name.strip()
        existing = customer_repository.get_tier_by_name(db, cleaned_name)
        if existing:
            raise DealFlowException(
                "A customer tier with this name already exists", status_code=400
            )

        return customer_repository.create_tier(
            db=db,
            name=cleaned_name,
            description=request.description,
            default_discount_limit=request.default_discount_limit,
            is_active=request.is_active,
        )

    def update_tier(
        self,
        db: Session,
        tier_id: uuid.UUID,
        request: CustomerTierUpdateRequest,
    ) -> CustomerTier:
        """
        Update an existing customer tier.
        Validates existence, name uniqueness (if changed), and applies valid updates.
        """
        tier = self.get_tier_by_id(db, tier_id)

        updates = request.model_dump(exclude_unset=True)
        if not updates:
            return tier

        if "name" in updates and updates["name"] is not None:
            cleaned_name = updates["name"].strip()
            if cleaned_name.lower() != tier.name.lower():
                existing = customer_repository.get_tier_by_name(db, cleaned_name)
                if existing and existing.id != tier.id:
                    raise DealFlowException(
                        "A customer tier with this name already exists",
                        status_code=400,
                    )
            updates["name"] = cleaned_name

        if "description" in updates and updates["description"] is not None:
            updates["description"] = updates["description"].strip()

        return customer_repository.update_tier(db, tier, updates)

    def deactivate_tier(self, db: Session, tier_id: uuid.UUID) -> CustomerTier:
        """
        Deactivate a customer tier following the logical-deactivation convention.
        Validates existence and ensures referenced tiers are never physically deleted.
        """
        tier = self.get_tier_by_id(db, tier_id)
        return customer_repository.deactivate_tier(db, tier)

    def create_customer(
        self, db: Session, request: CustomerCreate
    ) -> Customer:
        """
        Create a new B2B customer.
        Validates required fields and confirms that the requested customer tier exists and is active.
        """
        cleaned_name = request.name.strip()
        if not cleaned_name:
            raise DealFlowException("Customer name cannot be empty", status_code=400)

        tier = customer_repository.get_tier_by_id(db, request.customer_tier_id)
        if not tier:
            raise ResourceNotFoundError("Customer tier not found")

        if not tier.is_active:
            raise DealFlowException(
                "Cannot assign an inactive customer tier", status_code=400
            )

        return customer_repository.create_customer(
            db=db,
            name=cleaned_name,
            customer_tier_id=request.customer_tier_id,
            email=request.email,
            phone=request.phone,
            billing_address=request.billing_address,
            shipping_address=request.shipping_address,
            is_active=request.is_active,
        )

    def list_customers(
        self,
        db: Session,
        search: Optional[str] = None,
        customer_tier_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Customer]:
        """
        List and search B2B customers.
        Respects lifecycle state (defaults to active customers only) and delegates querying to repository.
        """
        cleaned_search = search.strip() if search else None
        return customer_repository.list_customers(
            db=db,
            search=cleaned_search,
            customer_tier_id=customer_tier_id,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

    def get_customer_by_id(
        self, db: Session, customer_id: uuid.UUID
    ) -> Customer:
        """
        Retrieve a customer by ID with associated customer tier.
        Raises ResourceNotFoundError if customer does not exist.
        """
        customer = customer_repository.get_customer_with_tier(
            db, customer_id
        )
        if not customer:
            raise ResourceNotFoundError("Customer not found")
        return customer

    def update_customer(
        self,
        db: Session,
        customer_id: uuid.UUID,
        request: CustomerUpdate,
    ) -> Customer:
        """
        Update an existing B2B customer record.
        Validates existence, applies supplied fields, and validates changed tier if applicable.
        """
        customer = customer_repository.get_customer_by_id(db, customer_id)
        if not customer:
            raise ResourceNotFoundError("Customer not found")

        updates = request.model_dump(exclude_unset=True)
        if not updates:
            return customer

        if "name" in updates and updates["name"] is not None:
            cleaned_name = updates["name"].strip()
            if not cleaned_name:
                raise DealFlowException("Customer name cannot be empty", status_code=400)
            updates["name"] = cleaned_name

        if "email" in updates and updates["email"] is not None:
            updates["email"] = updates["email"].strip() or None

        if "phone" in updates and updates["phone"] is not None:
            updates["phone"] = updates["phone"].strip() or None

        if "billing_address" in updates and updates["billing_address"] is not None:
            updates["billing_address"] = updates["billing_address"].strip() or None

        if "shipping_address" in updates and updates["shipping_address"] is not None:
            updates["shipping_address"] = updates["shipping_address"].strip() or None

        if "customer_tier_id" in updates and updates["customer_tier_id"] is not None:
            new_tier_id = updates["customer_tier_id"]
            if new_tier_id != customer.customer_tier_id:
                tier = customer_repository.get_tier_by_id(db, new_tier_id)
                if not tier:
                    raise ResourceNotFoundError("Customer tier not found")
                if not tier.is_active:
                    raise DealFlowException(
                        "Cannot assign an inactive customer tier", status_code=400
                    )

        return customer_repository.update_customer(db, customer, updates)

    def deactivate_customer(
        self, db: Session, customer_id: uuid.UUID
    ) -> Customer:
        """
        Deactivate a customer following logical-deactivation convention.
        Validates existence and ensures referenced customers are never physically deleted.
        """
        customer = customer_repository.get_customer_by_id(db, customer_id)
        if not customer:
            raise ResourceNotFoundError("Customer not found")

        # Determine whether the customer has existing references from business records
        is_referenced = customer_repository.is_customer_referenced(db, customer_id)

        # In accordance with project conventions and to preserve historical records,
        # perform logical deactivation so the customer cannot be selected for new business
        return customer_repository.deactivate_customer(db, customer)

    def get_customer_quotations(
        self,
        db: Session,
        customer_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Quotation]:
        """
        Retrieve quotations belonging to a specific customer.
        Verifies customer existence and retrieves their quotation records from the repository.
        """
        customer = customer_repository.get_customer_by_id(db, customer_id)
        if not customer:
            raise ResourceNotFoundError("Customer not found")

        return customer_repository.list_customer_quotations(
            db=db, customer_id=customer_id, skip=skip, limit=limit
        )

    def get_customer_orders(
        self,
        db: Session,
        customer_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """
        Retrieve orders belonging to a specific customer.
        Verifies customer existence and retrieves their order records from the repository.
        """
        customer = customer_repository.get_customer_by_id(db, customer_id)
        if not customer:
            raise ResourceNotFoundError("Customer not found")

        return customer_repository.list_customer_orders(
            db=db, customer_id=customer_id, skip=skip, limit=limit
        )

    def get_customer_subscriptions(
        self,
        db: Session,
        customer_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Subscription]:
        """
        Retrieve subscriptions belonging to a specific customer.
        Verifies customer existence and retrieves their subscription records from the repository.
        """
        customer = customer_repository.get_customer_by_id(db, customer_id)
        if not customer:
            raise ResourceNotFoundError("Customer not found")

        return customer_repository.list_customer_subscriptions(
            db=db, customer_id=customer_id, skip=skip, limit=limit
        )

    def ensure_customer_for_user(
        self,
        db: Session,
        user: User,
        explicit_customer_id: Optional[uuid.UUID] = None,
    ) -> Optional[Customer]:
        """
        Synchronize and enforce the canonical 1-to-1 relationship between User (with role CUSTOMER)
        and Customer.
        - If role is not CUSTOMER, ensures user.customer_id is None.
        - If explicit_customer_id is provided, validates that the customer exists and is not
          already associated with another user.
        - If not provided, reuses existing user.customer_id, or safely matches an unlinked customer
          with identical email, or creates a new customer business entity.
        - Flushes changes to session without premature external commits.
        """
        if user.role != UserRole.CUSTOMER:
            if user.customer_id is not None:
                user.customer_id = None
                db.flush()
            return None

        # If user already has a valid linked customer and no explicit customer override is given
        if explicit_customer_id is None and user.customer_id is not None:
            existing = customer_repository.get_customer_by_id(db, user.customer_id)
            if existing:
                return existing

        target_customer_id = explicit_customer_id

        if target_customer_id is not None:
            customer = customer_repository.get_customer_by_id(db, target_customer_id)
            if not customer:
                raise ResourceNotFoundError(f"Customer with id '{target_customer_id}' not found")

            # Check if another user is already associated with this customer
            stmt = select(User).where(User.customer_id == target_customer_id, User.id != user.id)
            other_user = db.scalars(stmt).first()
            if other_user:
                raise DealFlowException(
                    "This customer record is already associated with another user",
                    status_code=400,
                )

            user.customer_id = customer.id
            db.flush()
            return customer

        # Attempt to match an existing unlinked customer with matching email
        if user.email:
            matching_customer = customer_repository.get_customer_by_email(db, user.email)
            if matching_customer:
                # Check whether linked to another user
                stmt = select(User).where(
                    User.customer_id == matching_customer.id, User.id != user.id
                )
                linked_user = db.scalars(stmt).first()
                if not linked_user:
                    user.customer_id = matching_customer.id
                    db.flush()
                    return matching_customer

        # No unlinked customer found: create new Customer record
        tier = customer_repository.get_default_tier(db)
        new_customer = Customer(
            name=user.name,
            email=user.email,
            customer_tier_id=tier.id,
            is_active=user.is_active,
        )
        db.add(new_customer)
        db.flush()

        user.customer_id = new_customer.id
        db.flush()
        return new_customer

    def sync_all_customer_users(self, db: Session) -> int:
        """
        Idempotent batch synchronization: ensures all existing CUSTOMER users
        have a linked Customer record and non-customer users have customer_id=None.
        Returns count of customer users synchronized.
        """
        non_customer_users = db.scalars(
            select(User).where(User.role != UserRole.CUSTOMER, User.customer_id.isnot(None))
        ).all()
        for u in non_customer_users:
            u.customer_id = None

        customer_users = db.scalars(
            select(User).where(User.role == UserRole.CUSTOMER)
        ).all()
        synced_count = 0
        for u in customer_users:
            self.ensure_customer_for_user(db, u)
            synced_count += 1

        db.commit()
        return synced_count


customer_service = CustomerService()
