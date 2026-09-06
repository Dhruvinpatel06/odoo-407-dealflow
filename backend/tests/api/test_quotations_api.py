"""API tests for Quotation workflow, recalculation, and discount governance integration."""

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


def _create_auth_headers(user: User) -> dict:
    """Helper to generate Authorization header for a user."""
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sales_rep_user(db: Session) -> User:
    user = User(
        name="Sales Rep",
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
def customer_portal_user(db: Session) -> User:
    user = User(
        name="Portal User",
        email=f"portal-{uuid.uuid4().hex[:6]}@client.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def active_customer(db: Session) -> Customer:
    tier = CustomerTier(
        name=f"Gold-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("15.00"),
        is_active=True,
    )
    db.add(tier)
    db.flush()

    customer = Customer(
        name="Acme Corp",
        email=f"acme-{uuid.uuid4().hex[:6]}@acme.com",
        customer_tier_id=tier.id,
        is_active=True,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@pytest.fixture
def active_product(db: Session) -> Product:
    cat = ProductCategory(
        name=f"Hardware-{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db.add(cat)
    db.flush()

    prod = Product(
        sku=f"SKU-{uuid.uuid4().hex[:6]}",
        name="Enterprise Laptop",
        unit="PCS",
        base_price=Decimal("1000.00"),
        cost_price=Decimal("600.00"),
        tax_rate=Decimal("0.00"),
        category_id=cat.id,
        is_active=True,
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


class TestQuotationLifecycleAPI:
    """Tests for core quotation lifecycle endpoints."""

    def test_create_quotation(self, client: TestClient, sales_rep_user: User, active_customer: Customer):
        headers = _create_auth_headers(sales_rep_user)
        payload = {"customer_id": str(active_customer.id)}

        res = client.post("/api/v1/quotations", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["customer_id"] == str(active_customer.id)
        assert data["sales_rep_id"] == str(sales_rep_user.id)
        assert data["status"] == QuotationStatus.DRAFT.value
        assert float(data["subtotal"]) == 0.0
        assert data["approval_required"] is False

    def test_customer_role_forbidden_on_internal_quotation_api(
        self, client: TestClient, customer_portal_user: User, active_customer: Customer
    ):
        headers = _create_auth_headers(customer_portal_user)
        res = client.post(
            "/api/v1/quotations",
            json={"customer_id": str(active_customer.id)},
            headers=headers,
        )
        assert res.status_code == 403

    def test_unauthenticated_request_rejected(self, client: TestClient):
        res = client.get("/api/v1/quotations")
        assert res.status_code == 401


class TestQuotationDiscountRiskIntegrationAPI:
    """Tests for Discount Rules, Recalculate, Risk, and Submission endpoints."""

    def test_recalculate_and_risk_endpoints_no_violation(
        self,
        client: TestClient,
        sales_rep_user: User,
        active_customer: Customer,
        active_product: Product,
        db: Session,
    ):
        # Configure Tier Rule: max 15% discount
        rule = DiscountRule(
            customer_tier_id=active_customer.customer_tier_id,
            max_discount_percent=Decimal("15.00"),
            priority=1,
            is_active=True,
        )
        db.add(rule)
        db.commit()

        headers = _create_auth_headers(sales_rep_user)

        # 1. Create quotation
        q_res = client.post(
            "/api/v1/quotations",
            json={"customer_id": str(active_customer.id)},
            headers=headers,
        )
        q_id = q_res.json()["id"]

        # 2. Add line with requested discount = 10% (below 15% ceiling)
        line_res = client.post(
            f"/api/v1/quotations/{q_id}/lines",
            json={
                "product_id": str(active_product.id),
                "quantity": 2,
                "discount_percent": 10.0,
                "tax_rate": 5.0,
            },
            headers=headers,
        )
        assert line_res.status_code == 201
        line_data = line_res.json()
        assert len(line_data["lines"]) == 1
        line = line_data["lines"][0]

        # Assert authoritative snapshots
        assert float(line["allowed_discount_percent"]) == 15.0
        assert float(line["discount_excess_percent"]) == 0.0
        assert float(line_data["risk_score"]) == 0.0
        assert line_data["approval_required"] is False

        # 3. Call GET /api/v1/quotations/{id}/risk
        risk_res = client.get(f"/api/v1/quotations/{q_id}/risk", headers=headers)
        assert risk_res.status_code == 200
        risk_data = risk_res.json()
        assert risk_data["approval_required"] is False
        assert float(risk_data["risk_score"]) == 0.0
        assert risk_data["violating_lines_count"] == 0
        assert len(risk_data["line_risks"]) == 1
        assert risk_data["line_risks"][0]["is_violation"] is False

        # 4. Call POST /api/v1/quotations/{id}/recalculate
        recalc_res = client.post(
            f"/api/v1/quotations/{q_id}/recalculate", headers=headers
        )
        assert recalc_res.status_code == 200
        recalc_data = recalc_res.json()
        assert recalc_data["quotation"]["approval_required"] is False
        assert float(recalc_data["risk"]["risk_score"]) == 0.0

    def test_line_discount_violation_triggers_risk_and_approval(
        self,
        client: TestClient,
        sales_rep_user: User,
        active_customer: Customer,
        active_product: Product,
        db: Session,
    ):
        # Configure Category Rule: max 10% discount
        rule = DiscountRule(
            category_id=active_product.category_id,
            max_discount_percent=Decimal("10.00"),
            priority=5,
            is_active=True,
        )
        db.add(rule)
        db.commit()

        headers = _create_auth_headers(sales_rep_user)

        # 1. Create quotation
        q_res = client.post(
            "/api/v1/quotations",
            json={"customer_id": str(active_customer.id)},
            headers=headers,
        )
        q_id = q_res.json()["id"]

        # 2. Add line with requested discount = 14% (exceeds 10% ceiling by 4%)
        line_res = client.post(
            f"/api/v1/quotations/{q_id}/lines",
            json={
                "product_id": str(active_product.id),
                "quantity": 1,
                "discount_percent": 14.0,
            },
            headers=headers,
        )
        assert line_res.status_code == 201
        line_data = line_res.json()
        assert len(line_data["lines"]) == 1
        line = line_data["lines"][0]

        # Snapshot check
        assert float(line["allowed_discount_percent"]) == 10.0
        assert float(line["discount_excess_percent"]) == 4.0
        assert line_data["approval_required"] is True
        assert line_data["current_approval_level"] == ApproverRole.SALES_MANAGER.value
        # Risk score: single line with 4.0% excess -> 4.0 * 2 = 8.00
        assert float(line_data["risk_score"]) == 8.0

        # 3. Verify risk endpoint
        risk_res = client.get(f"/api/v1/quotations/{q_id}/risk", headers=headers)
        assert risk_res.status_code == 200
        risk_data = risk_res.json()
        assert risk_data["approval_required"] is True
        assert risk_data["required_approval_level"] == ApproverRole.SALES_MANAGER.value
        assert risk_data["violating_lines_count"] == 1
        assert risk_data["line_risks"][0]["is_violation"] is True
        assert float(risk_data["line_risks"][0]["discount_excess_percent"]) == 4.0

    def test_submit_quotation_recalculates_and_routes_to_pending_approval(
        self,
        client: TestClient,
        sales_rep_user: User,
        active_customer: Customer,
        active_product: Product,
        db: Session,
    ):
        # Configure Tier Rule: max 12%
        rule = DiscountRule(
            customer_tier_id=active_customer.customer_tier_id,
            max_discount_percent=Decimal("12.00"),
            priority=1,
            is_active=True,
        )
        db.add(rule)
        db.commit()

        headers = _create_auth_headers(sales_rep_user)

        # Create quotation & add line with requested discount = 20%
        q_res = client.post(
            "/api/v1/quotations",
            json={"customer_id": str(active_customer.id)},
            headers=headers,
        )
        q_id = q_res.json()["id"]

        client.post(
            f"/api/v1/quotations/{q_id}/lines",
            json={
                "product_id": str(active_product.id),
                "quantity": 1,
                "discount_percent": 20.0,
            },
            headers=headers,
        )

        # Submit quotation
        submit_res = client.post(
            f"/api/v1/quotations/{q_id}/submit", headers=headers
        )
        assert submit_res.status_code == 200
        submit_data = submit_res.json()
        assert submit_data["status"] == QuotationStatus.PENDING_APPROVAL.value
        assert submit_data["approval_required"] is True
        assert submit_data["current_approval_level"] == ApproverRole.SALES_MANAGER.value

    def test_submit_quotation_without_violation_approves_immediately(
        self,
        client: TestClient,
        sales_rep_user: User,
        active_customer: Customer,
        active_product: Product,
        db: Session,
    ):
        # Tier rule allows 15%
        rule = DiscountRule(
            customer_tier_id=active_customer.customer_tier_id,
            max_discount_percent=Decimal("15.00"),
            priority=1,
            is_active=True,
        )
        db.add(rule)
        db.commit()

        headers = _create_auth_headers(sales_rep_user)

        # Create quote & add line with 5% discount
        q_res = client.post(
            "/api/v1/quotations",
            json={"customer_id": str(active_customer.id)},
            headers=headers,
        )
        q_id = q_res.json()["id"]

        client.post(
            f"/api/v1/quotations/{q_id}/lines",
            json={
                "product_id": str(active_product.id),
                "quantity": 1,
                "discount_percent": 5.0,
            },
            headers=headers,
        )

        # Submit quote
        submit_res = client.post(
            f"/api/v1/quotations/{q_id}/submit", headers=headers
        )
        assert submit_res.status_code == 200
        submit_data = submit_res.json()
        assert submit_data["status"] == QuotationStatus.APPROVED.value
        assert submit_data["approval_required"] is False
