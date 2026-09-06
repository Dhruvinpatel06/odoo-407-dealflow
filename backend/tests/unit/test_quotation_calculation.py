"""Unit tests for pure QuotationCalculationEngine.

Validates:
- Line-level financial calculations (totals, taxes, costs, margins)
- Quotation aggregates (subtotal, total discounts, order discount %, taxes, totals, margins)
- Authoritative blended discount-risk score formula, boundary conditions, weighting, determinism
- Approval requirement and required approval level determination
"""

from decimal import Decimal

from app.common.enums import ApproverRole
from app.models.approval_policy import ApprovalPolicy
from app.modules.quotations.engine import QuotationCalculationEngine, quotation_engine


class TestLineFinancials:
    """Tests for calculate_line_financials."""

    def test_standard_line_calculation(self):
        fin = quotation_engine.calculate_line_financials(
            quantity=Decimal("2.00"),
            unit_price=Decimal("100.00"),
            discount_percent=Decimal("10.00"),
            tax_rate=Decimal("5.00"),
            unit_cost=Decimal("60.00"),
        )
        # Gross = 2 * 100 = 200.00
        # Discount = 200 * 0.10 = 20.00
        # Taxable = 200 - 20 = 180.00
        # Tax = 180 * 0.05 = 9.00
        # Line total = 180 + 9 = 189.00
        # Cost = 2 * 60 = 120.00
        # Margin amount = 180 - 120 = 60.00
        # Margin percent = (60 / 180) * 100 = 33.33%
        assert fin["gross_amount"] == Decimal("200.00")
        assert fin["discount_amount"] == Decimal("20.00")
        assert fin["taxable_amount"] == Decimal("180.00")
        assert fin["tax_amount"] == Decimal("9.00")
        assert fin["line_total"] == Decimal("189.00")
        assert fin["cost_amount"] == Decimal("120.00")
        assert fin["margin_amount"] == Decimal("60.00")
        assert fin["margin_percent"] == Decimal("33.33")

    def test_zero_discount_zero_tax(self):
        fin = quotation_engine.calculate_line_financials(
            quantity=Decimal("1.00"),
            unit_price=Decimal("50.00"),
            discount_percent=Decimal("0.00"),
            tax_rate=Decimal("0.00"),
            unit_cost=Decimal("30.00"),
        )
        assert fin["gross_amount"] == Decimal("50.00")
        assert fin["discount_amount"] == Decimal("0.00")
        assert fin["taxable_amount"] == Decimal("50.00")
        assert fin["tax_amount"] == Decimal("0.00")
        assert fin["line_total"] == Decimal("50.00")
        assert fin["margin_amount"] == Decimal("20.00")
        assert fin["margin_percent"] == Decimal("40.00")

    def test_one_hundred_percent_discount(self):
        fin = quotation_engine.calculate_line_financials(
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            discount_percent=Decimal("100.00"),
            tax_rate=Decimal("10.00"),
            unit_cost=Decimal("40.00"),
        )
        assert fin["gross_amount"] == Decimal("100.00")
        assert fin["discount_amount"] == Decimal("100.00")
        assert fin["taxable_amount"] == Decimal("0.00")
        assert fin["line_total"] == Decimal("0.00")
        assert fin["margin_amount"] == Decimal("-40.00")
        assert fin["margin_percent"] == Decimal("0.00")


class TestBlendedDiscountRiskScore:
    """Dedicated unit tests for the authoritative blended discount risk formula."""

    def test_empty_quotation_lines_returns_zero(self):
        score = quotation_engine.calculate_blended_risk_score([])
        assert score == Decimal("0.00")

    def test_no_line_violations_returns_zero(self):
        lines = [
            {
                "quantity": Decimal("2.00"),
                "unit_price": Decimal("100.00"),
                "discount_excess_percent": Decimal("0.00"),
            },
            {
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("300.00"),
                "discount_excess_percent": Decimal("0.00"),
            },
        ]
        score = quotation_engine.calculate_blended_risk_score(lines)
        assert score == Decimal("0.00")

    def test_single_line_violation(self):
        # Line 1: 1 * 100 = 100, excess = 2.00%
        # Line 2: 1 * 100 = 100, excess = 0.00%
        # Total gross = 200
        # W = (100 / 200) * 2.0 = 1.00
        # max_excess = 2.00
        # S = 0.5 * 2.0 + 0.5 * 1.0 = 1.50
        # Penalty = 0 (only 1 violation)
        # Raw = 1.50 * 2.0 = 3.00
        lines = [
            {
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("100.00"),
                "discount_excess_percent": Decimal("2.00"),
            },
            {
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("100.00"),
                "discount_excess_percent": Decimal("0.00"),
            },
        ]
        score = quotation_engine.calculate_blended_risk_score(lines)
        assert score == Decimal("3.00")

    def test_multiple_violating_lines_penalty(self):
        # 3 violating lines:
        # Each line: value 100, excess 3.00%
        # Total gross = 300
        # W = 3.00, max_excess = 3.00
        # S = 3.00
        # Penalty = min(5.0 * (3 - 1), 15.0) = 10.00
        # Raw = (3.00 * 2.0) + 10.00 = 16.00
        lines = [
            {
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("100.00"),
                "discount_excess_percent": Decimal("3.00"),
            },
            {
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("100.00"),
                "discount_excess_percent": Decimal("3.00"),
            },
            {
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("100.00"),
                "discount_excess_percent": Decimal("3.00"),
            },
        ]
        score = quotation_engine.calculate_blended_risk_score(lines)
        assert score == Decimal("16.00")

    def test_value_weighting_impact(self):
        # Higher dollar line with excess creates higher risk than lower dollar line
        small_line_violation = [
            {
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("10.00"),
                "discount_excess_percent": Decimal("5.00"),
            },
            {
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("990.00"),
                "discount_excess_percent": Decimal("0.00"),
            },
        ]
        large_line_violation = [
            {
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("990.00"),
                "discount_excess_percent": Decimal("5.00"),
            },
            {
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("10.00"),
                "discount_excess_percent": Decimal("0.00"),
            },
        ]
        small_score = quotation_engine.calculate_blended_risk_score(small_line_violation)
        large_score = quotation_engine.calculate_blended_risk_score(large_line_violation)
        assert large_score > small_score

    def test_boundary_capping_at_100(self):
        # Excessive discount excess (e.g. 60% excess) must cap at 100.00
        lines = [
            {
                "quantity": Decimal("10.00"),
                "unit_price": Decimal("1000.00"),
                "discount_excess_percent": Decimal("60.00"),
            }
        ]
        score = quotation_engine.calculate_blended_risk_score(lines)
        assert score == Decimal("100.00")

    def test_zero_value_quotation_with_excess(self):
        # Quantity or price is 0, but excess is reported
        lines = [
            {
                "quantity": Decimal("0.00"),
                "unit_price": Decimal("0.00"),
                "discount_excess_percent": Decimal("5.00"),
            }
        ]
        score = quotation_engine.calculate_blended_risk_score(lines)
        # 5.00 * 2.0 = 10.00
        assert score == Decimal("10.00")

    def test_repeated_calculation_is_deterministic(self):
        lines = [
            {
                "quantity": Decimal("3.50"),
                "unit_price": Decimal("149.99"),
                "discount_excess_percent": Decimal("4.25"),
            },
            {
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("250.00"),
                "discount_excess_percent": Decimal("1.50"),
            },
        ]
        score1 = quotation_engine.calculate_blended_risk_score(lines)
        score2 = quotation_engine.calculate_blended_risk_score(lines)
        score3 = quotation_engine.calculate_blended_risk_score(lines)
        assert score1 == score2 == score3


class TestApprovalRequirementDetermination:
    """Tests for approval requirement and approval level logic."""

    def test_no_violations_no_policies(self):
        app_req, level = quotation_engine.determine_approval_requirement(
            risk_score=Decimal("0.00"),
            has_line_violations=False,
            approval_policies=[],
        )
        assert app_req is False
        assert level is None

    def test_violations_without_policies_defaults_to_sales_manager(self):
        app_req, level = quotation_engine.determine_approval_requirement(
            risk_score=Decimal("5.00"),
            has_line_violations=True,
            approval_policies=[],
        )
        assert app_req is True
        assert level == ApproverRole.SALES_MANAGER.value

    def test_policy_matching_sales_manager(self):
        policy_mgr = ApprovalPolicy(
            name="Manager Tier",
            min_risk_score=Decimal("1.00"),
            max_risk_score=Decimal("20.00"),
            requires_manager=True,
            requires_finance=False,
            priority=10,
            is_active=True,
        )
        app_req, level = quotation_engine.determine_approval_requirement(
            risk_score=Decimal("12.00"),
            has_line_violations=True,
            approval_policies=[policy_mgr],
        )
        assert app_req is True
        assert level == ApproverRole.SALES_MANAGER.value

    def test_policy_matching_finance_operations(self):
        policy_mgr = ApprovalPolicy(
            name="Manager Tier",
            min_risk_score=Decimal("1.00"),
            max_risk_score=Decimal("20.00"),
            requires_manager=True,
            requires_finance=False,
            priority=10,
            is_active=True,
        )
        policy_fin = ApprovalPolicy(
            name="Finance Tier",
            min_risk_score=Decimal("20.01"),
            max_risk_score=Decimal("100.00"),
            requires_manager=True,
            requires_finance=True,
            priority=20,
            is_active=True,
        )
        app_req, level = quotation_engine.determine_approval_requirement(
            risk_score=Decimal("35.00"),
            has_line_violations=True,
            approval_policies=[policy_mgr, policy_fin],
        )
        assert app_req is True
        assert level == ApproverRole.FINANCE_OPERATIONS.value


class TestQuotationAggregates:
    """Tests for calculate_quotation_aggregates."""

    def test_aggregates_calculation(self):
        lines_fin = [
            {
                "gross_amount": Decimal("100.00"),
                "discount_amount": Decimal("10.00"),
                "tax_amount": Decimal("5.00"),
                "line_total": Decimal("95.00"),
                "cost_amount": Decimal("60.00"),
            },
            {
                "gross_amount": Decimal("200.00"),
                "discount_amount": Decimal("30.00"),
                "tax_amount": Decimal("10.00"),
                "line_total": Decimal("180.00"),
                "cost_amount": Decimal("110.00"),
            },
        ]
        aggs = quotation_engine.calculate_quotation_aggregates(lines_fin)
        assert aggs["subtotal"] == Decimal("300.00")
        assert aggs["discount_amount"] == Decimal("40.00")
        assert aggs["order_discount_percent"] == Decimal("13.33")
        assert aggs["tax_amount"] == Decimal("15.00")
        assert aggs["total_amount"] == Decimal("275.00")
        assert aggs["total_cost"] == Decimal("170.00")
        # Net subtotal = 300 - 40 = 260.00
        # Margin amount = 260 - 170 = 90.00
        # Margin percent = (90 / 260) * 100 = 34.62%
        assert aggs["margin_amount"] == Decimal("90.00")
        assert aggs["margin_percent"] == Decimal("34.62")
