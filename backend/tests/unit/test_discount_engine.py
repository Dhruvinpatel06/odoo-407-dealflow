"""Unit tests for DealFlow360 Discount Governance & Resolution Engine."""

from __future__ import annotations

import uuid
from decimal import Decimal
import pytest

from app.core.exceptions import DealFlowException
from app.models.discount_rule import DiscountRule
from app.modules.discounts.engine import discount_engine


def _create_rule(
    customer_tier_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    max_discount_percent: str = "10.00",
    priority: int = 0,
    is_active: bool = True,
) -> DiscountRule:
    """Helper to instantiate a DiscountRule domain object for engine testing."""
    return DiscountRule(
        id=uuid.uuid4(),
        customer_tier_id=customer_tier_id,
        category_id=category_id,
        max_discount_percent=Decimal(max_discount_percent),
        priority=priority,
        is_active=is_active,
    )


# TEST 1 — No rules (No tier rule, no category rule)
def test_discount_engine_no_rules():
    """Verify explicit no-rule behavior when neither tier nor category rules exist."""
    tier_id = uuid.uuid4()
    cat_id = uuid.uuid4()

    result = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("12.00"),
        customer_tier_id=tier_id,
        category_id=cat_id,
        discount_rules=[],
    )

    assert result.has_applicable_rule is False
    assert result.applicable_discount_limit is None
    assert result.allowed_discount_percent == Decimal("12.00")
    assert result.discount_excess_percent == Decimal("0.00")
    assert result.is_violation is False
    assert result.applied_rule_id is None
    assert "No applicable" in result.resolution_summary


# TEST 2 — Only tier rule (Requested below limit)
def test_discount_engine_only_tier_rule_within_limit():
    """Verify tier-only rule allows requested discount when within limit."""
    tier_id = uuid.uuid4()
    rule = _create_rule(customer_tier_id=tier_id, max_discount_percent="10.00")

    result = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("8.00"),
        customer_tier_id=tier_id,
        category_id=None,
        discount_rules=[rule],
    )

    assert result.has_applicable_rule is True
    assert result.applicable_discount_limit == Decimal("10.00")
    assert result.allowed_discount_percent == Decimal("8.00")
    assert result.discount_excess_percent == Decimal("0.00")
    assert result.is_violation is False
    assert result.applied_rule_id == rule.id
    assert result.applied_rule_type == "TIER"


# TEST 3 — Tier rule exceeded
def test_discount_engine_tier_rule_exceeded():
    """Verify tier rule caps allowed discount and reports violation when exceeded."""
    tier_id = uuid.uuid4()
    rule = _create_rule(customer_tier_id=tier_id, max_discount_percent="10.00")

    result = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("12.00"),
        customer_tier_id=tier_id,
        category_id=None,
        discount_rules=[rule],
    )

    assert result.has_applicable_rule is True
    assert result.applicable_discount_limit == Decimal("10.00")
    assert result.allowed_discount_percent == Decimal("10.00")
    assert result.discount_excess_percent == Decimal("2.00")
    assert result.is_violation is True
    assert result.applied_rule_id == rule.id


# TEST 4 — Only category rule (Requested within limit)
def test_discount_engine_only_category_rule_within_limit():
    """Verify category-only rule allows requested discount when within limit."""
    cat_id = uuid.uuid4()
    rule = _create_rule(category_id=cat_id, max_discount_percent="15.00")

    result = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("12.00"),
        customer_tier_id=None,
        category_id=cat_id,
        discount_rules=[rule],
    )

    assert result.has_applicable_rule is True
    assert result.applicable_discount_limit == Decimal("15.00")
    assert result.allowed_discount_percent == Decimal("12.00")
    assert result.discount_excess_percent == Decimal("0.00")
    assert result.is_violation is False
    assert result.applied_rule_id == rule.id
    assert result.applied_rule_type == "CATEGORY"


# TEST 5 — Category rule exceeded
def test_discount_engine_category_rule_exceeded():
    """Verify category rule caps allowed discount and reports violation when exceeded."""
    cat_id = uuid.uuid4()
    rule = _create_rule(category_id=cat_id, max_discount_percent="15.00")

    result = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("18.00"),
        customer_tier_id=None,
        category_id=cat_id,
        discount_rules=[rule],
    )

    assert result.has_applicable_rule is True
    assert result.applicable_discount_limit == Decimal("15.00")
    assert result.allowed_discount_percent == Decimal("15.00")
    assert result.discount_excess_percent == Decimal("3.00")
    assert result.is_violation is True


# TEST 6 — Both rules, tier stricter
def test_discount_engine_both_rules_tier_stricter():
    """Verify stricter tier limit wins when both tier and category rules apply."""
    tier_id = uuid.uuid4()
    cat_id = uuid.uuid4()
    tier_rule = _create_rule(customer_tier_id=tier_id, max_discount_percent="10.00")
    cat_rule = _create_rule(category_id=cat_id, max_discount_percent="15.00")

    result = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("12.00"),
        customer_tier_id=tier_id,
        category_id=cat_id,
        discount_rules=[tier_rule, cat_rule],
    )

    assert result.has_applicable_rule is True
    assert result.applicable_discount_limit == Decimal("10.00")
    assert result.allowed_discount_percent == Decimal("10.00")
    assert result.discount_excess_percent == Decimal("2.00")
    assert result.is_violation is True
    assert result.applied_rule_id == tier_rule.id
    assert result.applied_rule_type == "TIER"


# TEST 7 — Both rules, category stricter
def test_discount_engine_both_rules_category_stricter():
    """Verify stricter category limit wins when both tier and category rules apply."""
    tier_id = uuid.uuid4()
    cat_id = uuid.uuid4()
    tier_rule = _create_rule(customer_tier_id=tier_id, max_discount_percent="20.00")
    cat_rule = _create_rule(category_id=cat_id, max_discount_percent="10.00")

    result = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("12.00"),
        customer_tier_id=tier_id,
        category_id=cat_id,
        discount_rules=[tier_rule, cat_rule],
    )

    assert result.has_applicable_rule is True
    assert result.applicable_discount_limit == Decimal("10.00")
    assert result.allowed_discount_percent == Decimal("10.00")
    assert result.discount_excess_percent == Decimal("2.00")
    assert result.is_violation is True
    assert result.applied_rule_id == cat_rule.id
    assert result.applied_rule_type == "CATEGORY"


# TEST 8 — Requested exactly equals limit
def test_discount_engine_requested_equals_limit():
    """Verify requested discount exactly at the limit is allowed without violation."""
    tier_id = uuid.uuid4()
    rule = _create_rule(customer_tier_id=tier_id, max_discount_percent="10.00")

    result = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("10.00"),
        customer_tier_id=tier_id,
        discount_rules=[rule],
    )

    assert result.applicable_discount_limit == Decimal("10.00")
    assert result.allowed_discount_percent == Decimal("10.00")
    assert result.discount_excess_percent == Decimal("0.00")
    assert result.is_violation is False


# TEST 9 — Requested below limit
def test_discount_engine_requested_below_limit():
    """Verify requested discount below the limit is allowed with 0 excess."""
    tier_id = uuid.uuid4()
    rule = _create_rule(customer_tier_id=tier_id, max_discount_percent="10.00")

    result = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("5.00"),
        customer_tier_id=tier_id,
        discount_rules=[rule],
    )

    assert result.allowed_discount_percent == Decimal("5.00")
    assert result.discount_excess_percent == Decimal("0.00")
    assert result.is_violation is False


# TEST 10 — Inactive rule ignored
def test_discount_engine_inactive_rule_ignored():
    """Verify inactive discount rules never participate in governance."""
    tier_id = uuid.uuid4()
    cat_id = uuid.uuid4()
    active_tier_rule = _create_rule(
        customer_tier_id=tier_id, max_discount_percent="10.00", is_active=True
    )
    inactive_cat_rule = _create_rule(
        category_id=cat_id, max_discount_percent="5.00", is_active=False
    )

    result = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("8.00"),
        customer_tier_id=tier_id,
        category_id=cat_id,
        discount_rules=[active_tier_rule, inactive_cat_rule],
    )

    assert result.applicable_discount_limit == Decimal("10.00")
    assert result.allowed_discount_percent == Decimal("8.00")
    assert result.discount_excess_percent == Decimal("0.00")
    assert result.is_violation is False
    assert result.applied_rule_id == active_tier_rule.id


# TEST 11 — Customer has no tier
def test_discount_engine_customer_has_no_tier():
    """Verify customer without tier ignores tier rules but still evaluates category rules."""
    cat_id = uuid.uuid4()
    cat_rule = _create_rule(category_id=cat_id, max_discount_percent="15.00")

    result = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("20.00"),
        customer_tier_id=None,
        category_id=cat_id,
        discount_rules=[cat_rule],
    )

    assert result.applicable_discount_limit == Decimal("15.00")
    assert result.allowed_discount_percent == Decimal("15.00")
    assert result.discount_excess_percent == Decimal("5.00")
    assert result.is_violation is True


# TEST 12 — Product has no category
def test_discount_engine_product_has_no_category():
    """Verify product without category ignores category rules but evaluates tier rules."""
    tier_id = uuid.uuid4()
    tier_rule = _create_rule(customer_tier_id=tier_id, max_discount_percent="10.00")

    result = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("12.00"),
        customer_tier_id=tier_id,
        category_id=None,
        discount_rules=[tier_rule],
    )

    assert result.applicable_discount_limit == Decimal("10.00")
    assert result.allowed_discount_percent == Decimal("10.00")
    assert result.discount_excess_percent == Decimal("2.00")
    assert result.is_violation is True


# TEST 13 — Both tier and category missing
def test_discount_engine_both_tier_and_category_missing():
    """Verify neither tier nor category present returns clean unrestricted result without error."""
    result = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("10.00"),
        customer_tier_id=None,
        category_id=None,
        discount_rules=[],
    )

    assert result.has_applicable_rule is False
    assert result.applicable_discount_limit is None
    assert result.allowed_discount_percent == Decimal("10.00")
    assert result.discount_excess_percent == Decimal("0.00")
    assert result.is_violation is False


# TEST 14 — Multiple applicable rules and priority precedence
def test_discount_engine_priority_precedence():
    """Verify higher priority rule wins within the same condition scope."""
    tier_id = uuid.uuid4()
    low_priority_rule = _create_rule(
        customer_tier_id=tier_id, max_discount_percent="20.00", priority=1
    )
    high_priority_rule = _create_rule(
        customer_tier_id=tier_id, max_discount_percent="15.00", priority=5
    )

    result = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("18.00"),
        customer_tier_id=tier_id,
        discount_rules=[low_priority_rule, high_priority_rule],
    )

    assert result.applicable_discount_limit == Decimal("15.00")
    assert result.applied_rule_id == high_priority_rule.id
    assert result.allowed_discount_percent == Decimal("15.00")
    assert result.discount_excess_percent == Decimal("3.00")
    assert result.is_violation is True


# TEST 15 — Boundary precision testing
def test_discount_engine_boundary_precision():
    """Verify Decimal arithmetic around the boundary precision (10.00% vs 10.01%)."""
    tier_id = uuid.uuid4()
    rule = _create_rule(customer_tier_id=tier_id, max_discount_percent="10.00")

    # Boundary: exactly 10.00%
    res_exact = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("10.00"),
        customer_tier_id=tier_id,
        discount_rules=[rule],
    )
    assert res_exact.is_violation is False
    assert res_exact.discount_excess_percent == Decimal("0.00")

    # Boundary + 0.01% -> violation
    res_over = discount_engine.resolve_line_discount(
        requested_discount_percent=Decimal("10.01"),
        customer_tier_id=tier_id,
        discount_rules=[rule],
    )
    assert res_over.is_violation is True
    assert res_over.discount_excess_percent == Decimal("0.01")
    assert res_over.allowed_discount_percent == Decimal("10.00")


# TEST 16 — Negative or invalid requested discount rejected
def test_discount_engine_invalid_requested_discount():
    """Verify negative requested discount and values > 100 raise DealFlowException."""
    tier_id = uuid.uuid4()

    with pytest.raises(DealFlowException) as exc_neg:
        discount_engine.resolve_line_discount(
            requested_discount_percent=Decimal("-1.00"),
            customer_tier_id=tier_id,
        )
    assert exc_neg.value.status_code == 400
    assert "negative" in exc_neg.value.message.lower()

    with pytest.raises(DealFlowException) as exc_over:
        discount_engine.resolve_line_discount(
            requested_discount_percent=Decimal("100.50"),
            customer_tier_id=tier_id,
        )
    assert exc_over.value.status_code == 400
    assert "100" in exc_over.value.message
