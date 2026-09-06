"""Discount Rules service layer."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import DealFlowException, ResourceNotFoundError
from app.models.discount_rule import DiscountRule
from app.models.user import User
from app.modules.audit.service import audit_service
from app.modules.discounts.engine import discount_engine
from app.modules.discounts.repository import discount_repository
from app.modules.discounts.schemas import (
    DiscountGovernanceResult,
    DiscountRuleCreateRequest,
    DiscountRuleUpdateRequest,
)


def _rule_to_audit_dict(rule: DiscountRule) -> Dict[str, Any]:
    """Format discount rule state for audit log snapshot storage."""
    return {
        "id": str(rule.id),
        "customer_tier_id": str(rule.customer_tier_id) if rule.customer_tier_id else None,
        "category_id": str(rule.category_id) if rule.category_id else None,
        "max_discount_percent": str(rule.max_discount_percent),
        "priority": rule.priority,
        "is_active": rule.is_active,
    }


class DiscountService:
    """Coordinates business workflows, audit generation, and persistence for discount rules."""

    def get_discount_rule(self, db: Session, rule_id: uuid.UUID) -> DiscountRule:
        """Fetch discount rule by UUID, ensuring existence."""
        rule = discount_repository.get_discount_rule_by_id(db, rule_id)
        if not rule:
            raise ResourceNotFoundError("Discount rule not found")
        return rule

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
        return discount_repository.list_discount_rules(
            db=db,
            customer_tier_id=customer_tier_id,
            category_id=category_id,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

    def create_discount_rule(
        self,
        db: Session,
        request: DiscountRuleCreateRequest,
        current_user: Optional[User] = None,
    ) -> DiscountRule:
        """
        Create a new discount rule with referenced entity validation, conflict detection,
        and authoritative audit logging.
        """
        discount_engine.validate_rule_configuration(
            customer_tier_id=request.customer_tier_id,
            category_id=request.category_id,
            max_discount_percent=request.max_discount_percent,
            priority=request.priority,
        )

        if request.customer_tier_id is not None:
            tier = discount_repository.get_customer_tier(db, request.customer_tier_id)
            if not tier:
                raise ResourceNotFoundError("Customer tier not found")
            if not tier.is_active:
                raise DealFlowException("Customer tier is inactive", status_code=400)

        if request.category_id is not None:
            category = discount_repository.get_product_category(db, request.category_id)
            if not category:
                raise ResourceNotFoundError("Product category not found")
            if not category.is_active:
                raise DealFlowException("Product category is inactive", status_code=400)

        if request.is_active:
            existing_rules = discount_repository.find_active_rules_by_conditions(
                db, request.customer_tier_id, request.category_id
            )
            discount_engine.detect_conflicts(
                existing_rules=existing_rules,
                customer_tier_id=request.customer_tier_id,
                category_id=request.category_id,
                priority=request.priority,
            )

        rule = discount_repository.create_discount_rule(
            db=db,
            customer_tier_id=request.customer_tier_id,
            category_id=request.category_id,
            max_discount_percent=request.max_discount_percent,
            priority=request.priority,
            is_active=request.is_active,
        )

        # Record authoritative backend audit log
        audit_service.log_event(
            db=db,
            entity_type="DISCOUNT_RULE",
            entity_id=rule.id,
            action="CREATE",
            user_id=current_user.id if current_user else None,
            old_values=None,
            new_values=_rule_to_audit_dict(rule),
            reason=f"Created discount rule with {rule.max_discount_percent}% ceiling",
        )

        db.commit()
        db.refresh(rule)
        return rule

    def update_discount_rule(
        self,
        db: Session,
        rule_id: uuid.UUID,
        request: DiscountRuleUpdateRequest,
        current_user: Optional[User] = None,
    ) -> DiscountRule:
        """
        Update an existing discount rule with configuration validation and authoritative audit logging.
        """
        rule = self.get_discount_rule(db, rule_id)
        updates = request.model_dump(exclude_unset=True)

        if not updates:
            return rule

        # Capture backend-derived old state before mutation
        old_values = _rule_to_audit_dict(rule)

        target_tier_id = (
            updates["customer_tier_id"]
            if "customer_tier_id" in updates
            else rule.customer_tier_id
        )
        target_category_id = (
            updates["category_id"]
            if "category_id" in updates
            else rule.category_id
        )
        target_max_discount = (
            updates["max_discount_percent"]
            if "max_discount_percent" in updates
            else rule.max_discount_percent
        )
        target_priority = (
            updates["priority"]
            if "priority" in updates
            else rule.priority
        )
        target_is_active = (
            updates["is_active"]
            if "is_active" in updates
            else rule.is_active
        )

        discount_engine.validate_rule_configuration(
            customer_tier_id=target_tier_id,
            category_id=target_category_id,
            max_discount_percent=target_max_discount,
            priority=target_priority,
        )

        if "customer_tier_id" in updates and updates["customer_tier_id"] is not None:
            tier = discount_repository.get_customer_tier(db, updates["customer_tier_id"])
            if not tier:
                raise ResourceNotFoundError("Customer tier not found")
            if not tier.is_active:
                raise DealFlowException("Customer tier is inactive", status_code=400)

        if "category_id" in updates and updates["category_id"] is not None:
            category = discount_repository.get_product_category(db, updates["category_id"])
            if not category:
                raise ResourceNotFoundError("Product category not found")
            if not category.is_active:
                raise DealFlowException("Product category is inactive", status_code=400)

        if target_is_active:
            existing_rules = discount_repository.find_active_rules_by_conditions(
                db, target_tier_id, target_category_id
            )
            discount_engine.detect_conflicts(
                existing_rules=existing_rules,
                customer_tier_id=target_tier_id,
                category_id=target_category_id,
                priority=target_priority,
                rule_id=rule.id,
            )

        updated_rule = discount_repository.update_discount_rule(db, rule, updates)
        new_values = _rule_to_audit_dict(updated_rule)

        # Distinguish activation, deactivation, or general update
        if updates.get("is_active") is True and old_values.get("is_active") is False:
            action = "ACTIVATE"
            reason = "Activated discount rule"
        elif updates.get("is_active") is False and old_values.get("is_active") is True:
            action = "DEACTIVATE"
            reason = "Deactivated discount rule"
        else:
            action = "UPDATE"
            reason = "Updated discount rule configuration"

        audit_service.log_event(
            db=db,
            entity_type="DISCOUNT_RULE",
            entity_id=updated_rule.id,
            action=action,
            user_id=current_user.id if current_user else None,
            old_values=old_values,
            new_values=new_values,
            reason=reason,
        )

        db.commit()
        db.refresh(updated_rule)
        return updated_rule

    def deactivate_discount_rule(
        self,
        db: Session,
        rule_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> DiscountRule:
        """
        Logically deactivate a discount rule (preserves row for audit/history) and record audit log.
        """
        rule = self.get_discount_rule(db, rule_id)
        if not rule.is_active:
            return rule

        old_values = _rule_to_audit_dict(rule)
        updated_rule = discount_repository.deactivate_discount_rule(db, rule)
        new_values = _rule_to_audit_dict(updated_rule)

        audit_service.log_event(
            db=db,
            entity_type="DISCOUNT_RULE",
            entity_id=updated_rule.id,
            action="DEACTIVATE",
            user_id=current_user.id if current_user else None,
            old_values=old_values,
            new_values=new_values,
            reason="Deactivated discount rule via delete endpoint",
        )

        db.commit()
        db.refresh(updated_rule)
        return updated_rule

    def evaluate_line_governance(
        self,
        db: Session,
        requested_discount_percent: Decimal,
        customer_tier_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
    ) -> DiscountGovernanceResult:
        """
        Orchestrate discount governance evaluation:
        1. Fetch applicable active discount rules from repository.
        2. Apply deterministic discount engine resolution.
        """
        applicable_rules = discount_repository.get_applicable_rules(
            db=db,
            customer_tier_id=customer_tier_id,
            category_id=category_id,
        )
        return discount_engine.resolve_line_discount(
            requested_discount_percent=requested_discount_percent,
            customer_tier_id=customer_tier_id,
            category_id=category_id,
            discount_rules=applicable_rules,
        )

    def evaluate_quotation_line(
        self,
        db: Session,
        quotation_line: Any,
        customer_tier_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
    ) -> DiscountGovernanceResult:
        """
        Orchestrate discount governance evaluation for a QuotationLine domain instance.
        Resolves customer tier and product category context if not explicitly provided.
        """
        effective_category_id = category_id
        if effective_category_id is None:
            product = getattr(quotation_line, "product", None)
            if product is not None:
                effective_category_id = getattr(product, "category_id", None)

        effective_tier_id = customer_tier_id
        if effective_tier_id is None:
            quotation = getattr(quotation_line, "quotation", None)
            if quotation is not None:
                customer = getattr(quotation, "customer", None)
                if customer is not None:
                    effective_tier_id = getattr(customer, "customer_tier_id", None)

        requested_discount = getattr(
            quotation_line, "discount_percent", Decimal("0.00")
        )

        return self.evaluate_line_governance(
            db=db,
            requested_discount_percent=requested_discount,
            customer_tier_id=effective_tier_id,
            category_id=effective_category_id,
        )


discount_service = DiscountService()
