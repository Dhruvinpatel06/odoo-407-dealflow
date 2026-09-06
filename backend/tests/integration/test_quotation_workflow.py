"""Integration tests for DealFlow360 Quotation Discount Governance Workflow.

Covers all 17 integration test scenarios specified in Step 4:
- TEST 1: Single line, no discount violation
- TEST 2: Single line violation
- TEST 3: Multiple quotation lines (evaluates every line)
- TEST 4: Multiple violating lines (multi-line risk penalty)
- TEST 5: Tier stricter than category
- TEST 6: Category stricter than tier
- TEST 7: Inactive rule ignored
- TEST 8: Quantity change triggers recalculation
- TEST 9: Product change resolves new category rule
- TEST 10: Pricing change triggers recalculation
- TEST 11: Discount change triggers recalculation
- TEST 12: Customer tier change re-evaluates limits
- TEST 13: Recalculate endpoint complete refresh
- TEST 14: Risk endpoint authoritative explanation
- TEST 15: Repeated recalculation determinism
- TEST 16: Zero-line quotation handling
- TEST 17: Zero-value quotation handling
- Stale state submission recalculation
- Approval policies integration (Manager vs Finance)
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import ApproverRole, QuotationStatus, UserRole
from app.core.security import create_access_token, hash_password
from app.models.approval_policy import ApprovalPolicy
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.discount_rule import DiscountRule
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.user import User
from app.modules.quotations.service import quotation_service


def _auth_headers(user: User) -> dict:
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sales_rep(db: Session) -> User:
    user = User(
        name="Sales Representative",
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
def tier_gold(db: Session) -> CustomerTier:
    tier = CustomerTier(
        name=f"Gold-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("15.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


@pytest.fixture
def tier_platinum(db: Session) -> CustomerTier:
    tier = CustomerTier(
        name=f"Platinum-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("25.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


@pytest.fixture
def customer_gold(db: Session, tier_gold: CustomerTier) -> Customer:
    customer = Customer(
        name="Gold Enterprise Corp",
        email=f"gold-{uuid.uuid4().hex[:6]}@enterprise.com",
        customer_tier_id=tier_gold.id,
        is_active=True,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@pytest.fixture
def cat_hardware(db: Session) -> ProductCategory:
    cat = ProductCategory(
        name=f"Hardware-{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@pytest.fixture
def cat_services(db: Session) -> ProductCategory:
    cat = ProductCategory(
        name=f"Services-{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@pytest.fixture
def product_laptop(db: Session, cat_hardware: ProductCategory) -> Product:
    prod = Product(
        sku=f"LAPTOP-{uuid.uuid4().hex[:6]}",
        name="Business Laptop",
        unit="PCS",
        base_price=Decimal("1000.00"),
        cost_price=Decimal("600.00"),
        tax_rate=Decimal("5.00"),
        category_id=cat_hardware.id,
        is_active=True,
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


@pytest.fixture
def product_service(db: Session, cat_services: ProductCategory) -> Product:
    prod = Product(
        sku=f"SERVICE-{uuid.uuid4().hex[:6]}",
        name="Deployment Service",
        unit="HRS",
        base_price=Decimal("200.00"),
        cost_price=Decimal("100.00"),
        tax_rate=Decimal("0.00"),
        category_id=cat_services.id,
        is_active=True,
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


class TestQuotationDiscountEngineIntegration:
    """17 Specific Integration Tests for Quotation Discount Governance."""

    # TEST 1: Single line, no discount violation
    def test_01_single_line_no_violation(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, product_laptop: Product, db: Session
    ):
        # Tier limit = 10%, Category limit = 15%
        db.add(DiscountRule(customer_tier_id=customer_gold.customer_tier_id, max_discount_percent=Decimal("10.00"), priority=1, is_active=True))
        db.add(DiscountRule(category_id=product_laptop.category_id, max_discount_percent=Decimal("15.00"), priority=1, is_active=True))
        db.commit()

        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        
        # Requested discount = 8%
        res = client.post(
            f"/api/v1/quotations/{q['id']}/lines",
            json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 8.0},
            headers=headers,
        ).json()

        line = res["lines"][0]
        assert float(line["allowed_discount_percent"]) == 10.0
        assert float(line["discount_excess_percent"]) == 0.0
        assert float(res["risk_score"]) == 0.0
        assert res["approval_required"] is False

    # TEST 2: Single line violation
    def test_02_single_line_violation(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, product_laptop: Product, db: Session
    ):
        # Tier limit = 10%, Category limit = 15%
        db.add(DiscountRule(customer_tier_id=customer_gold.customer_tier_id, max_discount_percent=Decimal("10.00"), priority=1, is_active=True))
        db.add(DiscountRule(category_id=product_laptop.category_id, max_discount_percent=Decimal("15.00"), priority=1, is_active=True))
        db.commit()

        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()

        # Requested discount = 12%
        res = client.post(
            f"/api/v1/quotations/{q['id']}/lines",
            json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 12.0},
            headers=headers,
        ).json()

        line = res["lines"][0]
        assert float(line["allowed_discount_percent"]) == 10.0
        assert float(line["discount_excess_percent"]) == 2.0
        assert float(res["risk_score"]) > 0.0
        assert res["approval_required"] is True

    # TEST 3: Multiple quotation lines (Line 1 ok, Line 2 violation, Line 3 ok)
    def test_03_multiple_lines_evaluation(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, product_laptop: Product, product_service: Product, db: Session
    ):
        db.add(DiscountRule(customer_tier_id=customer_gold.customer_tier_id, max_discount_percent=Decimal("10.00"), priority=1, is_active=True))
        db.commit()

        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()

        # Line 1: 5% (no violation)
        client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 5.0}, headers=headers)
        # Line 2: 15% (violation, excess 5%)
        client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_service.id), "quantity": 2, "discount_percent": 15.0}, headers=headers)
        # Line 3: 8% (no violation)
        res = client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 8.0}, headers=headers).json()

        assert len(res["lines"]) == 3
        # Check every line was evaluated
        assert float(res["lines"][0]["discount_excess_percent"]) == 0.0
        assert float(res["lines"][1]["discount_excess_percent"]) == 5.0
        assert float(res["lines"][2]["discount_excess_percent"]) == 0.0
        assert res["approval_required"] is True

    # TEST 4: Multiple violating lines
    def test_04_multiple_violating_lines(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, product_laptop: Product, product_service: Product, db: Session
    ):
        db.add(DiscountRule(customer_tier_id=customer_gold.customer_tier_id, max_discount_percent=Decimal("10.00"), priority=1, is_active=True))
        db.commit()

        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()

        # Line 1: 14% (excess 4%)
        client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 14.0}, headers=headers)
        # Line 2: 16% (excess 6%)
        res = client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_service.id), "quantity": 1, "discount_percent": 16.0}, headers=headers).json()

        risk = client.get(f"/api/v1/quotations/{q['id']}/risk", headers=headers).json()
        assert risk["violating_lines_count"] == 2
        assert risk["approval_required"] is True
        # Multi-line penalty adds at least 5.0 to score
        assert float(risk["risk_score"]) > 10.0

    # TEST 5: Tier stricter than category
    def test_05_tier_stricter_rule(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, product_laptop: Product, db: Session
    ):
        # Tier = 10%, Category = 15%, Requested = 12%
        db.add(DiscountRule(customer_tier_id=customer_gold.customer_tier_id, max_discount_percent=Decimal("10.00"), priority=1, is_active=True))
        db.add(DiscountRule(category_id=product_laptop.category_id, max_discount_percent=Decimal("15.00"), priority=1, is_active=True))
        db.commit()

        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        res = client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 12.0}, headers=headers).json()

        line = res["lines"][0]
        assert float(line["allowed_discount_percent"]) == 10.0
        assert float(line["discount_excess_percent"]) == 2.0
        assert res["approval_required"] is True

    # TEST 6: Category stricter than tier
    def test_06_category_stricter_rule(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, product_laptop: Product, db: Session
    ):
        # Tier = 20%, Category = 10%, Requested = 12%
        db.add(DiscountRule(customer_tier_id=customer_gold.customer_tier_id, max_discount_percent=Decimal("20.00"), priority=1, is_active=True))
        db.add(DiscountRule(category_id=product_laptop.category_id, max_discount_percent=Decimal("10.00"), priority=1, is_active=True))
        db.commit()

        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        res = client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 12.0}, headers=headers).json()

        line = res["lines"][0]
        assert float(line["allowed_discount_percent"]) == 10.0
        assert float(line["discount_excess_percent"]) == 2.0
        assert res["approval_required"] is True

    # TEST 7: Inactive rule ignored
    def test_07_inactive_rule_ignored(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, product_laptop: Product, db: Session
    ):
        # Inactive rule with 5% limit
        db.add(DiscountRule(customer_tier_id=customer_gold.customer_tier_id, max_discount_percent=Decimal("5.00"), priority=10, is_active=False))
        # Active rule with 20% limit
        db.add(DiscountRule(customer_tier_id=customer_gold.customer_tier_id, max_discount_percent=Decimal("20.00"), priority=1, is_active=True))
        db.commit()

        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        # Requested 15% -> Allowed under 20% active rule, would be violation under 5% inactive rule
        res = client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 15.0}, headers=headers).json()

        line = res["lines"][0]
        assert float(line["allowed_discount_percent"]) == 20.0
        assert float(line["discount_excess_percent"]) == 0.0
        assert res["approval_required"] is False

    # TEST 8: Quantity change triggers recalculation
    def test_08_quantity_change_triggers_recalculation(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, product_laptop: Product, db: Session
    ):
        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        q_line = client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 0.0}, headers=headers).json()

        line_id = q_line["lines"][0]["id"]
        assert float(q_line["subtotal"]) == 1000.0

        # Change quantity to 5
        updated = client.patch(
            f"/api/v1/quotations/{q['id']}/lines/{line_id}",
            json={"quantity": 5},
            headers=headers,
        ).json()
        assert float(updated["subtotal"]) == 5000.0
        assert float(updated["lines"][0]["quantity"]) == 5.0

    # TEST 9: Product change resolves new category rule
    def test_09_product_category_rule_resolution(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, product_laptop: Product, product_service: Product, db: Session
    ):
        # Hardware ceiling = 10%, Services ceiling = 25%
        db.add(DiscountRule(category_id=product_laptop.category_id, max_discount_percent=Decimal("10.00"), priority=1, is_active=True))
        db.add(DiscountRule(category_id=product_service.category_id, max_discount_percent=Decimal("25.00"), priority=1, is_active=True))
        db.commit()

        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()

        # Laptop with 15% discount -> violation (limit 10%)
        l1 = client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 15.0}, headers=headers).json()
        assert float(l1["lines"][0]["allowed_discount_percent"]) == 10.0
        assert float(l1["lines"][0]["discount_excess_percent"]) == 5.0

        # Service with 15% discount -> within limit (limit 25%)
        l2 = client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_service.id), "quantity": 1, "discount_percent": 15.0}, headers=headers).json()
        service_line = next(l for l in l2["lines"] if l["product_id"] == str(product_service.id))
        assert float(service_line["allowed_discount_percent"]) == 25.0
        assert float(service_line["discount_excess_percent"]) == 0.0

    # TEST 10: Pricing change triggers recalculation
    def test_10_pricing_change_triggers_recalculation(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, product_laptop: Product, db: Session
    ):
        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        res1 = client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 2}, headers=headers).json()
        line_id = res1["lines"][0]["id"]
        assert float(res1["subtotal"]) == 2000.0

        # Change unit_price on line
        res2 = client.patch(
            f"/api/v1/quotations/{q['id']}/lines/{line_id}",
            json={"unit_price": 1200.0},
            headers=headers,
        ).json()
        assert float(res2["subtotal"]) == 2400.0
        assert float(res2["lines"][0]["unit_price"]) == 1200.0

    # TEST 11: Discount change triggers recalculation
    def test_11_discount_change_triggers_recalculation(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, product_laptop: Product, db: Session
    ):
        db.add(DiscountRule(customer_tier_id=customer_gold.customer_tier_id, max_discount_percent=Decimal("10.00"), priority=1, is_active=True))
        db.commit()

        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        res1 = client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 5.0}, headers=headers).json()
        assert res1["approval_required"] is False
        line_id = res1["lines"][0]["id"]

        # Increase discount to 15% -> now triggers excess and approval
        res2 = client.patch(
            f"/api/v1/quotations/{q['id']}/lines/{line_id}",
            json={"discount_percent": 15.0},
            headers=headers,
        ).json()
        assert float(res2["lines"][0]["discount_excess_percent"]) == 5.0
        assert res2["approval_required"] is True

    # TEST 12: Customer tier change re-evaluates limits
    def test_12_customer_tier_change(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, tier_platinum: CustomerTier, product_laptop: Product, db: Session
    ):
        # Gold tier rule: 10%
        db.add(DiscountRule(customer_tier_id=customer_gold.customer_tier_id, max_discount_percent=Decimal("10.00"), priority=1, is_active=True))
        # Platinum tier rule: 25%
        db.add(DiscountRule(customer_tier_id=tier_platinum.id, max_discount_percent=Decimal("25.00"), priority=1, is_active=True))
        db.commit()

        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 18.0}, headers=headers)

        # Under Gold tier (10%), 18% discount is a violation
        risk_gold = client.get(f"/api/v1/quotations/{q['id']}/risk", headers=headers).json()
        assert risk_gold["approval_required"] is True
        assert float(risk_gold["line_risks"][0]["discount_excess_percent"]) == 8.0

        # Change customer's tier to Platinum (25% allowed)
        customer_gold.customer_tier_id = tier_platinum.id
        db.add(customer_gold)
        db.commit()

        # Recalculate quotation
        recalc = client.post(f"/api/v1/quotations/{q['id']}/recalculate", headers=headers).json()
        assert recalc["quotation"]["approval_required"] is False
        assert float(recalc["quotation"]["lines"][0]["allowed_discount_percent"]) == 25.0
        assert float(recalc["quotation"]["lines"][0]["discount_excess_percent"]) == 0.0

    # TEST 13: Recalculate endpoint
    def test_13_recalculate_endpoint(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, product_laptop: Product, db: Session
    ):
        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 2, "discount_percent": 5.0}, headers=headers)

        res = client.post(f"/api/v1/quotations/{q['id']}/recalculate", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "quotation" in data
        assert "risk" in data
        assert "recalculated_at" in data

    # TEST 14: Risk endpoint
    def test_14_risk_endpoint(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, product_laptop: Product, db: Session
    ):
        db.add(DiscountRule(customer_tier_id=customer_gold.customer_tier_id, max_discount_percent=Decimal("10.00"), priority=1, is_active=True))
        db.commit()

        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 12.0}, headers=headers)

        res = client.get(f"/api/v1/quotations/{q['id']}/risk", headers=headers)
        assert res.status_code == 200
        risk = res.json()
        assert risk["quotation_id"] == q["id"]
        assert risk["approval_required"] is True
        assert len(risk["line_risks"]) == 1
        assert "formula_explanation" in risk

    # TEST 15: Repeated recalculation determinism
    def test_15_repeated_recalculation_determinism(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, product_laptop: Product, db: Session
    ):
        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 3, "discount_percent": 7.5}, headers=headers)

        r1 = client.post(f"/api/v1/quotations/{q['id']}/recalculate", headers=headers).json()
        r2 = client.post(f"/api/v1/quotations/{q['id']}/recalculate", headers=headers).json()
        r3 = client.post(f"/api/v1/quotations/{q['id']}/recalculate", headers=headers).json()

        assert r1["quotation"]["subtotal"] == r2["quotation"]["subtotal"] == r3["quotation"]["subtotal"]
        assert r1["risk"]["risk_score"] == r2["risk"]["risk_score"] == r3["risk"]["risk_score"]

    # TEST 16: Zero-line quotation handling
    def test_16_zero_line_quotation(
        self, client: TestClient, sales_rep: User, customer_gold: Customer
    ):
        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        risk = client.get(f"/api/v1/quotations/{q['id']}/risk", headers=headers).json()
        assert float(risk["risk_score"]) == 0.0
        assert risk["approval_required"] is False
        assert risk["total_lines_count"] == 0

    # TEST 17: Zero-value quotation handling
    def test_17_zero_value_quotation(
        self, client: TestClient, sales_rep: User, customer_gold: Customer, product_laptop: Product
    ):
        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        # Line with 0 quantity or 0 price
        client.post(
            f"/api/v1/quotations/{q['id']}/lines",
            json={"product_id": str(product_laptop.id), "quantity": 1, "unit_price": 0.0, "discount_percent": 0.0},
            headers=headers,
        )
        risk = client.get(f"/api/v1/quotations/{q['id']}/risk", headers=headers).json()
        assert float(risk["subtotal"]) == 0.0
        assert float(risk["risk_score"]) == 0.0
        assert risk["approval_required"] is False


class TestApprovalPolicyAndSubmissionWorkflows:
    """Tests for policy-based approval levels and submit recalculation."""

    def test_approval_policy_levels_manager_vs_finance(
        self,
        client: TestClient,
        sales_rep: User,
        customer_gold: Customer,
        product_laptop: Product,
        db: Session,
    ):
        # Configure Approval Policies:
        # Policy 1: Risk 1.00 to 10.00 -> Sales Manager
        db.add(ApprovalPolicy(name="Manager Policy", min_risk_score=Decimal("1.00"), max_risk_score=Decimal("10.00"), requires_manager=True, requires_finance=False, priority=10, is_active=True))
        # Policy 2: Risk > 10.00 -> Finance Operations
        db.add(ApprovalPolicy(name="Finance Policy", min_risk_score=Decimal("10.01"), max_risk_score=None, requires_manager=True, requires_finance=True, priority=20, is_active=True))
        # Discount rule: 10%
        db.add(DiscountRule(customer_tier_id=customer_gold.customer_tier_id, max_discount_percent=Decimal("10.00"), priority=1, is_active=True))
        db.commit()

        headers = _auth_headers(sales_rep)

        # Case A: Low excess (12% requested -> 2% excess -> risk score 4.00) -> matches Manager Policy
        q1 = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        client.post(f"/api/v1/quotations/{q1['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 12.0}, headers=headers)
        risk1 = client.get(f"/api/v1/quotations/{q1['id']}/risk", headers=headers).json()
        assert risk1["approval_required"] is True
        assert risk1["required_approval_level"] == ApproverRole.SALES_MANAGER.value

        # Case B: High excess (25% requested -> 15% excess -> risk score 30.00) -> matches Finance Policy
        q2 = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        client.post(f"/api/v1/quotations/{q2['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 25.0}, headers=headers)
        risk2 = client.get(f"/api/v1/quotations/{q2['id']}/risk", headers=headers).json()
        assert risk2["approval_required"] is True
        assert risk2["required_approval_level"] == ApproverRole.FINANCE_OPERATIONS.value

    def test_submission_recalculates_stale_quotation(
        self,
        client: TestClient,
        sales_rep: User,
        customer_gold: Customer,
        product_laptop: Product,
        db: Session,
    ):
        headers = _auth_headers(sales_rep)
        q = client.post("/api/v1/quotations", json={"customer_id": str(customer_gold.id)}, headers=headers).json()
        # Add line with 15% discount before any rule exists
        client.post(f"/api/v1/quotations/{q['id']}/lines", json={"product_id": str(product_laptop.id), "quantity": 1, "discount_percent": 15.0}, headers=headers)

        # Now an admin introduces a 10% discount rule in the background
        db.add(DiscountRule(customer_tier_id=customer_gold.customer_tier_id, max_discount_percent=Decimal("10.00"), priority=5, is_active=True))
        db.commit()

        # Submit without prior recalculation: submit MUST recalculate and catch the new violation
        submit_res = client.post(f"/api/v1/quotations/{q['id']}/submit", headers=headers).json()
        assert submit_res["status"] == QuotationStatus.PENDING_APPROVAL.value
        assert submit_res["approval_required"] is True
