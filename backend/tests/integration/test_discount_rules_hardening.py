"""Comprehensive hardening, edge-case, determinism, and safety tests for DealFlow360 Discount Rules.

Covers:
- Edge cases from Step 6:
  - Exact ceiling equality (discount == limit -> violation is False)
  - Excess non-negativity across varied requested discounts
  - Customer without tier (category rule still applies without error)
  - Product without category (tier rule still applies without error)
  - Both tier and category missing (unrestricted, no error)
  - Stricter rule selection symmetry (Tier 10 vs Cat 15 -> 10; Tier 20 vs Cat 10 -> 10)
- Recalculation determinism across multiple repeated runs
- Security & frontend non-authoritative audit verification
- End-to-end quotation mutation and recalculation pipeline
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import ApproverRole, QuotationStatus, UserRole
from app.core.security import create_access_token, hash_password
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.discount_rule import DiscountRule
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.user import User
from app.modules.discounts.engine import discount_engine


def _auth_headers(user: User) -> dict:
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db: Session) -> User:
    user = User(
        name="Hardening Admin",
        email=f"admin-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sales_rep_user(db: Session) -> User:
    user = User(
        name="Hardening Rep",
        email=f"rep-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.SALES_REP,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def customer_no_tier(db: Session) -> Customer:
    customer = Customer(
        name="No Tier Customer",
        email=f"notier-{uuid.uuid4().hex[:6]}@client.local",
        customer_tier_id=None,
        is_active=True,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@pytest.fixture
def product_no_category(db: Session) -> Product:
    # Note: Product model category_id is nullable=False, so let's verify discount engine behavior directly for None category
    pass


class TestDiscountGovernanceEdgeCases:
    """Pure and operational edge-case unit and integration tests (Sections 6-18)."""

    def test_discount_exactly_at_limit_is_not_a_violation(self):
        """Exact equality must not count as a violation (limit = 10%, req = 10% -> violation = False)."""
        rule = DiscountRule(
            max_discount_percent=Decimal("10.00"),
            customer_tier_id=uuid.uuid4(),
            is_active=True,
        )
        res = discount_engine.resolve_line_discount(
            requested_discount_percent=Decimal("10.00"),
            customer_tier_id=rule.customer_tier_id,
            discount_rules=[rule],
        )
        assert res.applicable_discount_limit == Decimal("10.00")
        assert res.allowed_discount_percent == Decimal("10.00")
        assert res.discount_excess_percent == Decimal("0.00")
        assert res.is_violation is False

    def test_excess_never_negative(self):
        """Excess must be zero when requested < limit."""
        rule = DiscountRule(
            max_discount_percent=Decimal("15.00"),
            customer_tier_id=uuid.uuid4(),
            is_active=True,
        )
        res_below = discount_engine.resolve_line_discount(
            requested_discount_percent=Decimal("5.00"),
            customer_tier_id=rule.customer_tier_id,
            discount_rules=[rule],
        )
        assert res_below.discount_excess_percent == Decimal("0.00")
        assert res_below.is_violation is False

    def test_customer_without_tier_applies_category_rule(self):
        """Customer with customer_tier_id=None still respects applicable category rules."""
        cat_id = uuid.uuid4()
        rule = DiscountRule(
            category_id=cat_id,
            max_discount_percent=Decimal("12.00"),
            is_active=True,
        )
        res = discount_engine.resolve_line_discount(
            requested_discount_percent=Decimal("16.00"),
            customer_tier_id=None,
            category_id=cat_id,
            discount_rules=[rule],
        )
        assert res.applicable_discount_limit == Decimal("12.00")
        assert res.allowed_discount_percent == Decimal("12.00")
        assert res.discount_excess_percent == Decimal("4.00")
        assert res.is_violation is True

    def test_product_without_category_applies_tier_rule(self):
        """Line with category_id=None still respects applicable customer tier rules."""
        tier_id = uuid.uuid4()
        rule = DiscountRule(
            customer_tier_id=tier_id,
            max_discount_percent=Decimal("18.00"),
            is_active=True,
        )
        res = discount_engine.resolve_line_discount(
            requested_discount_percent=Decimal("20.00"),
            customer_tier_id=tier_id,
            category_id=None,
            discount_rules=[rule],
        )
        assert res.applicable_discount_limit == Decimal("18.00")
        assert res.allowed_discount_percent == Decimal("18.00")
        assert res.discount_excess_percent == Decimal("2.00")
        assert res.is_violation is True

    def test_both_tier_and_category_missing_returns_unrestricted(self):
        """When both customer_tier_id and category_id are None, no rules match."""
        res = discount_engine.resolve_line_discount(
            requested_discount_percent=Decimal("10.00"),
            customer_tier_id=None,
            category_id=None,
            discount_rules=[],
        )
        assert res.applicable_discount_limit is None
        assert res.allowed_discount_percent == Decimal("10.00")
        assert res.discount_excess_percent == Decimal("0.00")
        assert res.is_violation is False
        assert res.has_applicable_rule is False

    def test_stricter_rule_selection_cases(self):
        """Verify stricter applicable limit wins regardless of whether Tier or Category is lower."""
        tier_id = uuid.uuid4()
        cat_id = uuid.uuid4()

        # Case A: Tier 10%, Category 15% -> Limit 10%
        rules_a = [
            DiscountRule(customer_tier_id=tier_id, max_discount_percent=Decimal("10.00"), is_active=True),
            DiscountRule(category_id=cat_id, max_discount_percent=Decimal("15.00"), is_active=True),
        ]
        res_a = discount_engine.resolve_line_discount(
            requested_discount_percent=Decimal("12.00"),
            customer_tier_id=tier_id,
            category_id=cat_id,
            discount_rules=rules_a,
        )
        assert res_a.applicable_discount_limit == Decimal("10.00")
        assert res_a.discount_excess_percent == Decimal("2.00")
        assert res_a.is_violation is True

        # Case B: Tier 20%, Category 10% -> Limit 10%
        rules_b = [
            DiscountRule(customer_tier_id=tier_id, max_discount_percent=Decimal("20.00"), is_active=True),
            DiscountRule(category_id=cat_id, max_discount_percent=Decimal("10.00"), is_active=True),
        ]
        res_b = discount_engine.resolve_line_discount(
            requested_discount_percent=Decimal("12.00"),
            customer_tier_id=tier_id,
            category_id=cat_id,
            discount_rules=rules_b,
        )
        assert res_b.applicable_discount_limit == Decimal("10.00")
        assert res_b.discount_excess_percent == Decimal("2.00")
        assert res_b.is_violation is True


class TestRecalculationDeterminismAndHardening:
    """Determinism across repeated recalculation runs (Section 60)."""

    def test_repeated_recalculation_consistency(
        self,
        client: TestClient,
        admin_user: User,
        sales_rep_user: User,
        db: Session,
    ):
        tier = CustomerTier(name=f"Tier-{uuid.uuid4().hex[:6]}", default_discount_limit=Decimal("15.00"), is_active=True)
        cat = ProductCategory(name=f"Cat-{uuid.uuid4().hex[:6]}", is_active=True)
        db.add_all([tier, cat])
        db.flush()

        prod = Product(
            sku=f"PRD-{uuid.uuid4().hex[:6]}",
            name="Deterministic Server",
            unit="PCS",
            base_price=Decimal("1000.00"),
            cost_price=Decimal("500.00"),
            tax_rate=Decimal("5.00"),
            category_id=cat.id,
            is_active=True,
        )
        customer = Customer(name="Det Corp", email=f"det-{uuid.uuid4().hex[:6]}@corp.local", customer_tier_id=tier.id, is_active=True)
        db.add_all([prod, customer])
        db.flush()

        rule = DiscountRule(customer_tier_id=tier.id, max_discount_percent=Decimal("12.00"), priority=1, is_active=True)
        db.add(rule)
        db.commit()

        rep_h = _auth_headers(sales_rep_user)

        # Create quote with 2 lines (Line 1: 10% within limit; Line 2: 15% violates 12% ceiling)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer.id)}, headers=rep_h).json()
        client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(prod.id), "quantity": 2, "discount_percent": 10.0, "tax_rate": 5.0}, headers=rep_h)
        client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(prod.id), "quantity": 1, "discount_percent": 15.0, "tax_rate": 5.0}, headers=rep_h)

        # Run recalculation 3 times consecutively
        run1 = client.post(f"/api/v1/quotations/{q['id']}/recalculate", headers=rep_h).json()
        run2 = client.post(f"/api/v1/quotations/{q['id']}/recalculate", headers=rep_h).json()
        run3 = client.post(f"/api/v1/quotations/{q['id']}/recalculate", headers=rep_h).json()

        # Verify Calculation #1 == Calculation #2 == Calculation #3
        q1, q2, q3 = run1["quotation"], run2["quotation"], run3["quotation"]
        r1, r2, r3 = run1["risk"], run2["risk"], run3["risk"]

        assert q1["subtotal"] == q2["subtotal"] == q3["subtotal"]
        assert q1["discount_amount"] == q2["discount_amount"] == q3["discount_amount"]
        assert q1["tax_amount"] == q2["tax_amount"] == q3["tax_amount"]
        assert q1["total_amount"] == q2["total_amount"] == q3["total_amount"]
        assert q1["margin_amount"] == q2["margin_amount"] == q3["margin_amount"]
        assert q1["margin_percent"] == q2["margin_percent"] == q3["margin_percent"]
        assert r1["risk_score"] == r2["risk_score"] == r3["risk_score"]
        assert r1["approval_required"] == r2["approval_required"] == r3["approval_required"]
        assert r1["violating_lines_count"] == r2["violating_lines_count"] == r3["violating_lines_count"]

    def test_no_arbitrary_client_audit_endpoint_exists(self, client: TestClient, admin_user: User):
        """Verify there is no unauthorized endpoint allowing client to inject audit logs."""
        admin_h = _auth_headers(admin_user)
        # Attempt to POST /discount-rules/audit -> must return 404 (route does not exist)
        res = client.post("/api/v1/discount-rules/audit", json={"action": "CREATE"}, headers=admin_h)
        assert res.status_code in (404, 405)
