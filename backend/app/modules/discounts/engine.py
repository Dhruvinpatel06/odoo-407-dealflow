"""Discount Rules business validation and governance engine."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, List, Optional

from app.core.exceptions import DealFlowException
from app.models.discount_rule import DiscountRule
from app.modules.discounts.schemas import DiscountGovernanceResult


class DiscountEngine:
    """
    Encapsulates deterministic business rules, configuration validation,
    and authoritative discount limit resolution for DealFlow360.
    """

    # --- Configuration Validation ---

    def validate_discount_limit(self, max_discount_percent: Decimal) -> None:
        """Validate discount percentage ceiling falls within the allowed 0.00 to 100.00 range."""
        if max_discount_percent < Decimal("0.00") or max_discount_percent > Decimal("100.00"):
            raise DealFlowException(
                "max_discount_percent must be between 0.00 and 100.00",
                status_code=400,
            )

    def validate_priority(self, priority: int) -> None:
        """Validate priority/precedence is a non-negative integer."""
        if priority < 0:
            raise DealFlowException(
                "Priority must be a non-negative integer",
                status_code=400,
            )

    def validate_conditions(
        self,
        customer_tier_id: Optional[uuid.UUID],
        category_id: Optional[uuid.UUID],
    ) -> None:
        """Ensure at least one governance condition (customer tier or product category) is specified."""
        if customer_tier_id is None and category_id is None:
            raise DealFlowException(
                "Discount rule must specify at least one condition: customer_tier_id or category_id",
                status_code=400,
            )

    def validate_rule_configuration(
        self,
        customer_tier_id: Optional[uuid.UUID],
        category_id: Optional[uuid.UUID],
        max_discount_percent: Decimal,
        priority: int,
    ) -> None:
        """Run complete logical validation for a proposed discount rule configuration."""
        self.validate_discount_limit(max_discount_percent)
        self.validate_priority(priority)
        self.validate_conditions(customer_tier_id, category_id)

    def detect_conflicts(
        self,
        existing_rules: List[DiscountRule],
        customer_tier_id: Optional[uuid.UUID],
        category_id: Optional[uuid.UUID],
        priority: int,
        rule_id: Optional[uuid.UUID] = None,
    ) -> None:
        """
        Check for conflicting rule configurations.
        Disallows multiple active rules with identical tier, category, and priority conditions.
        """
        for rule in existing_rules:
            if rule.id == rule_id:
                continue
            if not rule.is_active:
                continue
            if (
                rule.customer_tier_id == customer_tier_id
                and rule.category_id == category_id
                and rule.priority == priority
            ):
                raise DealFlowException(
                    "An active discount rule with identical customer tier, category, and priority already exists",
                    status_code=400,
                )

    # --- Authoritative Governance Resolution ---

    def resolve_line_discount(
        self,
        requested_discount_percent: Decimal,
        customer_tier_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
        discount_rules: Optional[List[DiscountRule]] = None,
    ) -> DiscountGovernanceResult:
        """
        Resolve authoritative discount governance for a quotation line.

        Business Rules:
        1. Inactive rules are strictly ignored.
        2. A rule is applicable if its scope matches the context:
           - Customer Tier match (when customer_tier_id is present)
           - Product Category match (when category_id is present)
           - Joint match (both customer_tier_id and category_id present)
        3. Within each scope, higher priority wins (priority DESC). Ties break by stricter limit.
        4. Across applicable scopes (Tier vs Category vs Joint), the stricter (lower) applicable limit wins.
        5. If no active rule applies, the discount is unrestricted (applicable_limit = None, allowed = requested).
        6. Allowed discount = min(requested, applicable_limit).
        7. Discount excess = max(requested - applicable_limit, 0).
        8. Violation = requested > applicable_limit.
        """
        # Validate requested discount value
        if requested_discount_percent < Decimal("0.00"):
            raise DealFlowException(
                "Requested discount cannot be negative", status_code=400
            )
        if requested_discount_percent > Decimal("100.00"):
            raise DealFlowException(
                "Requested discount cannot exceed 100.00%", status_code=400
            )

        req = round(requested_discount_percent, 2)
        active_rules = [r for r in (discount_rules or []) if r.is_active]

        # Scope classification
        joint_rules: List[DiscountRule] = []
        tier_rules: List[DiscountRule] = []
        category_rules: List[DiscountRule] = []

        for r in active_rules:
            is_tier_match = (
                customer_tier_id is not None and r.customer_tier_id == customer_tier_id
            )
            is_cat_match = (
                category_id is not None and r.category_id == category_id
            )

            if r.customer_tier_id is not None and r.category_id is not None:
                if is_tier_match and is_cat_match:
                    joint_rules.append(r)
            elif r.customer_tier_id is not None and is_tier_match:
                tier_rules.append(r)
            elif r.category_id is not None and is_cat_match:
                category_rules.append(r)

        # Select highest-priority rule within each scope (priority DESC, limit ASC)
        def _best_rule(scope_rules: List[DiscountRule]) -> Optional[DiscountRule]:
            if not scope_rules:
                return None
            return sorted(
                scope_rules,
                key=lambda x: (x.priority if x.priority is not None else 0, -x.max_discount_percent),
                reverse=True,
            )[0]

        best_joint = _best_rule(joint_rules)
        best_tier = _best_rule(tier_rules)
        best_category = _best_rule(category_rules)

        tier_limit = best_tier.max_discount_percent if best_tier else None
        category_limit = best_category.max_discount_percent if best_category else None

        candidates = [r for r in [best_joint, best_tier, best_category] if r is not None]

        # Case 1: No applicable rule configured
        if not candidates:
            return DiscountGovernanceResult(
                requested_discount_percent=req,
                allowed_discount_percent=req,
                applicable_discount_limit=None,
                discount_excess_percent=Decimal("0.00"),
                is_violation=False,
                has_applicable_rule=False,
                applied_rule_id=None,
                applied_rule_type=None,
                tier_rule_limit=tier_limit,
                category_rule_limit=category_limit,
                applied_tier_id=customer_tier_id,
                applied_category_id=category_id,
                resolution_summary="No applicable active discount rule configured",
            )

        # Cases 2, 3, 4: Stricter applicable limit wins
        # Sort candidates: lowest max_discount_percent wins; tie-break with higher priority
        winning_rule = sorted(
            candidates,
            key=lambda x: (x.max_discount_percent, -(x.priority if x.priority is not None else 0)),
        )[0]

        applicable_limit = round(winning_rule.max_discount_percent, 2)
        is_violation = req > applicable_limit
        allowed = min(req, applicable_limit)
        excess = max(req - applicable_limit, Decimal("0.00"))

        if winning_rule.customer_tier_id is not None and winning_rule.category_id is not None:
            applied_type = "TIER_AND_CATEGORY"
        elif winning_rule.customer_tier_id is not None:
            applied_type = "TIER"
        else:
            applied_type = "CATEGORY"

        summary = (
            f"Applied {applied_type} discount ceiling of {applicable_limit}% "
            f"(requested: {req}%, allowed: {allowed}%, excess: {excess}%)"
        )

        return DiscountGovernanceResult(
            requested_discount_percent=req,
            allowed_discount_percent=allowed,
            applicable_discount_limit=applicable_limit,
            discount_excess_percent=excess,
            is_violation=is_violation,
            has_applicable_rule=True,
            applied_rule_id=winning_rule.id,
            applied_rule_type=applied_type,
            tier_rule_limit=tier_limit,
            category_rule_limit=category_limit,
            applied_tier_id=customer_tier_id,
            applied_category_id=category_id,
            resolution_summary=summary,
        )

    def evaluate_quotation_line(
        self,
        quotation_line: Any,
        customer_tier_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
        discount_rules: Optional[List[DiscountRule]] = None,
    ) -> DiscountGovernanceResult:
        """
        Convenience wrapper to evaluate a QuotationLine domain instance.
        Extracts requested discount and falls back to line relationship IDs if not explicitly provided.
        """
        requested_discount = getattr(
            quotation_line, "discount_percent", Decimal("0.00")
        )

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

        return self.resolve_line_discount(
            requested_discount_percent=requested_discount,
            customer_tier_id=effective_tier_id,
            category_id=effective_category_id,
            discount_rules=discount_rules,
        )


discount_engine = DiscountEngine()
