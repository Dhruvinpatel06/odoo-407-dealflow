"""Quotations repository layer."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.common.enums import QuotationStatus
from app.models.approval_instance import ApprovalInstance
from app.models.approval_policy import ApprovalPolicy
from app.models.customer import Customer
from app.models.discount_rule import DiscountRule
from app.models.order import Order
from app.models.product import Product
from app.models.quotation import Quotation
from app.models.quotation_line import QuotationLine



class QuotationRepository:
    """Handles database queries and persistence for quotations and quotation lines."""

    def get_quotation_by_id(
        self, db: Session, quotation_id: uuid.UUID
    ) -> Optional[Quotation]:
        """Fetch a quotation with lines, customer, and catalog details eagerly loaded."""
        stmt = (
            select(Quotation)
            .options(
                joinedload(Quotation.customer).joinedload(Customer.tier),
                joinedload(Quotation.sales_rep),
                selectinload(Quotation.lines)
                .joinedload(QuotationLine.product)
                .joinedload(Product.category),
                selectinload(Quotation.lines).joinedload(QuotationLine.variant),
                selectinload(Quotation.approval_instances),
            )
            .where(Quotation.id == quotation_id)
        )
        return db.execute(stmt).unique().scalar_one_or_none()

    def get_quotation_by_number(
        self, db: Session, quotation_number: str
    ) -> Optional[Quotation]:
        """Fetch quotation by quotation number."""
        stmt = select(Quotation).where(Quotation.quotation_number == quotation_number)
        return db.execute(stmt).scalar_one_or_none()

    def list_quotations(
        self,
        db: Session,
        status: Optional[QuotationStatus] = None,
        customer_id: Optional[uuid.UUID] = None,
        sales_rep_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Quotation]:
        """List quotations with optional filters."""
        stmt = (
            select(Quotation)
            .options(
                joinedload(Quotation.customer),
                joinedload(Quotation.sales_rep),
                selectinload(Quotation.lines),
            )
            .order_by(Quotation.created_at.desc())
        )
        if status is not None:
            stmt = stmt.where(Quotation.status == status)
        if customer_id is not None:
            stmt = stmt.where(Quotation.customer_id == customer_id)
        if sales_rep_id is not None:
            stmt = stmt.where(Quotation.sales_rep_id == sales_rep_id)

        stmt = stmt.offset(skip).limit(limit)
        return list(db.execute(stmt).unique().scalars().all())

    def create_quotation(self, db: Session, quotation: Quotation) -> Quotation:
        """Persist a new quotation."""
        db.add(quotation)
        db.commit()
        db.refresh(quotation)
        return quotation

    def get_line_by_id(
        self, db: Session, quotation_id: uuid.UUID, line_id: uuid.UUID
    ) -> Optional[QuotationLine]:
        """Fetch a specific quotation line belonging to a quotation."""
        stmt = (
            select(QuotationLine)
            .options(
                joinedload(QuotationLine.product).joinedload(Product.category),
                joinedload(QuotationLine.variant),
            )
            .where(
                QuotationLine.id == line_id,
                QuotationLine.quotation_id == quotation_id,
            )
        )
        return db.execute(stmt).scalar_one_or_none()

    def add_line(self, db: Session, line: QuotationLine) -> QuotationLine:
        """Add and persist a quotation line."""
        db.add(line)
        db.flush()
        return line

    def delete_line(self, db: Session, line: QuotationLine) -> None:
        """Delete a quotation line."""
        db.delete(line)
        db.flush()

    def get_active_approval_policies(self, db: Session) -> List[ApprovalPolicy]:
        """Fetch all active approval policies ordered by priority DESC."""
        stmt = (
            select(ApprovalPolicy)
            .where(ApprovalPolicy.is_active.is_(True))
            .order_by(ApprovalPolicy.priority.desc(), ApprovalPolicy.min_risk_score.desc())
        )
        return list(db.execute(stmt).scalars().all())

    def get_active_discount_rules(self, db: Session) -> List[DiscountRule]:
        """Fetch all active discount rules ordered by priority DESC."""
        stmt = (
            select(DiscountRule)
            .where(DiscountRule.is_active.is_(True))
            .order_by(DiscountRule.priority.desc())
        )
        return list(db.execute(stmt).scalars().all())

    def save_recalculated_state(
        self, db: Session, quotation: Quotation
    ) -> Quotation:
        """Commit all recalculated quotation and line changes atomically."""
        db.add(quotation)
        db.commit()
        db.refresh(quotation)
        return quotation

    def delete_quotation(self, db: Session, quotation: Quotation) -> None:
        """Delete a quotation entity and commit."""
        db.delete(quotation)
        db.commit()


    def get_lines(
        self, db: Session, quotation_id: uuid.UUID
    ) -> List[QuotationLine]:
        """Fetch all lines belonging to a quotation."""
        stmt = (
            select(QuotationLine)
            .options(
                joinedload(QuotationLine.product).joinedload(Product.category),
                joinedload(QuotationLine.variant),
            )
            .where(QuotationLine.quotation_id == quotation_id)
            .order_by(QuotationLine.created_at.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def get_order_by_quotation_id(
        self, db: Session, quotation_id: uuid.UUID
    ) -> Optional[Order]:
        """Fetch order created from a quotation."""
        stmt = (
            select(Order)
            .options(joinedload(Order.customer), joinedload(Order.quotation))
            .where(Order.quotation_id == quotation_id)
        )
        return db.execute(stmt).scalar_one_or_none()

    def get_order_by_id(
        self, db: Session, order_id: uuid.UUID
    ) -> Optional[Order]:
        """Fetch order by primary key UUID."""
        stmt = (
            select(Order)
            .options(joinedload(Order.customer), joinedload(Order.quotation))
            .where(Order.id == order_id)
        )
        return db.execute(stmt).scalar_one_or_none()

    def list_orders(
        self,
        db: Session,
        customer_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """List confirmed sales orders with optional filters."""
        stmt = (
            select(Order)
            .options(joinedload(Order.customer), joinedload(Order.quotation))
            .order_by(Order.confirmed_at.desc())
        )
        if customer_id is not None:
            stmt = stmt.where(Order.customer_id == customer_id)
        if status is not None:
            stmt = stmt.where(Order.status == status)

        stmt = stmt.offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create_order(self, db: Session, order: Order) -> Order:
        """Persist order."""
        db.add(order)
        db.flush()
        return order

    def save_order(self, db: Session, order: Order) -> Order:
        """Commit order changes."""
        db.add(order)
        db.commit()
        db.refresh(order)
        return order

    def get_quotation_approval_instances(
        self, db: Session, quotation_id: uuid.UUID
    ) -> List[ApprovalInstance]:
        """Fetch all approval instances for a quotation with steps."""
        stmt = (
            select(ApprovalInstance)
            .options(selectinload(ApprovalInstance.steps))
            .where(ApprovalInstance.quotation_id == quotation_id)
            .order_by(ApprovalInstance.created_at.desc())
        )
        return list(db.execute(stmt).scalars().all())


    def get_all_quotations_for_pipeline(self, db: Session) -> List[Quotation]:
        """Fetch active quotations with customer and sales rep for Kanban pipeline."""
        stmt = (
            select(Quotation)
            .options(
                joinedload(Quotation.customer),
                joinedload(Quotation.sales_rep),
            )
            .order_by(Quotation.last_activity_at.desc())
        )
        return list(db.execute(stmt).unique().scalars().all())


quotation_repository = QuotationRepository()

