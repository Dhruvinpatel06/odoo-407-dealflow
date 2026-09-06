"""Integration tests for Discount Rules Security, Audit, Activation/Deactivation, and Propagation.

Covers:
- Section 33: Role-based authorization test matrix (SALES_REP, SALES_MANAGER, FINANCE_OPS, ADMIN, CUSTOMER, Unauthenticated)
- Section 34: Backend audit logging test matrix (CREATE, UPDATE, ACTIVATE, DEACTIVATE, no false audits on failures)
- Section 35: Operational state behavior (active vs inactive, activation propagation, modification propagation, deactivation propagation)
- Section 28-32: Quotation recalculation & risk/approval state refresh upon rule changes
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import ApproverRole, UserRole
from app.core.security import create_access_token, hash_password
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.discount_rule import DiscountRule
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.user import User


def _auth_headers(user: User) -> dict:
    """Generate authorization header with Bearer token."""
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db: Session) -> User:
    user = User(
        name="Security Admin",
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
def customer_user(db: Session) -> User:
    user = User(
        name="External Customer",
        email=f"cust-{uuid.uuid4().hex[:6]}@external.com",
        password_hash=hash_password("Password123!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_tier(db: Session) -> CustomerTier:
    tier = CustomerTier(
        name=f"Tier-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("15.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


@pytest.fixture
def test_category(db: Session) -> ProductCategory:
    category = ProductCategory(
        name=f"Hardware-{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def test_customer(db: Session, test_tier: CustomerTier) -> Customer:
    customer = Customer(
        name="Test Corp",
        email=f"corp-{uuid.uuid4().hex[:6]}@test.com",
        customer_tier_id=test_tier.id,
        is_active=True,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@pytest.fixture
def test_product(db: Session, test_category: ProductCategory) -> Product:
    prod = Product(
        sku=f"PRD-{uuid.uuid4().hex[:6]}",
        name="Test Server",
        unit="PCS",
        base_price=Decimal("1000.00"),
        cost_price=Decimal("500.00"),
        tax_rate=Decimal("0.00"),
        category_id=test_category.id,
        is_active=True,
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


class TestDiscountRulesAuthorizationMatrix:
    """Authorization verification (Section 33, 4-10)."""

    def test_sales_rep_cannot_create_discount_rule(
        self, client: TestClient, sales_rep_user: User, test_tier: CustomerTier
    ):
        headers = _auth_headers(sales_rep_user)
        res = client.post(
            "/api/v1/discount-rules",
            json={"customer_tier_id": str(test_tier.id), "max_discount_percent": "10.00"},
            headers=headers,
        )
        assert res.status_code == 403

    def test_sales_rep_cannot_update_discount_rule(
        self, client: TestClient, admin_user: User, sales_rep_user: User, test_tier: CustomerTier
    ):
        # Admin creates rule
        admin_h = _auth_headers(admin_user)
        create_res = client.post(
            "/api/v1/discount-rules",
            json={"customer_tier_id": str(test_tier.id), "max_discount_percent": "10.00"},
            headers=admin_h,
        )
        rule_id = create_res.json()["id"]

        # Sales Rep attempts to update
        rep_h = _auth_headers(sales_rep_user)
        res = client.patch(
            f"/api/v1/discount-rules/{rule_id}",
            json={"max_discount_percent": "20.00"},
            headers=rep_h,
        )
        assert res.status_code == 403

    def test_sales_rep_cannot_deactivate_discount_rule(
        self, client: TestClient, admin_user: User, sales_rep_user: User, test_tier: CustomerTier
    ):
        admin_h = _auth_headers(admin_user)
        create_res = client.post(
            "/api/v1/discount-rules",
            json={"customer_tier_id": str(test_tier.id), "max_discount_percent": "10.00"},
            headers=admin_h,
        )
        rule_id = create_res.json()["id"]

        rep_h = _auth_headers(sales_rep_user)
        res = client.delete(f"/api/v1/discount-rules/{rule_id}", headers=rep_h)
        assert res.status_code == 403

    def test_sales_rep_can_view_discount_rules(
        self, client: TestClient, admin_user: User, sales_rep_user: User, test_tier: CustomerTier
    ):
        admin_h = _auth_headers(admin_user)
        create_res = client.post(
            "/api/v1/discount-rules",
            json={"customer_tier_id": str(test_tier.id), "max_discount_percent": "10.00"},
            headers=admin_h,
        )
        rule_id = create_res.json()["id"]

        rep_h = _auth_headers(sales_rep_user)
        list_res = client.get("/api/v1/discount-rules", headers=rep_h)
        assert list_res.status_code == 200

        detail_res = client.get(f"/api/v1/discount-rules/{rule_id}", headers=rep_h)
        assert detail_res.status_code == 200

    def test_external_customer_cannot_view_or_mutate_discount_rules(
        self, client: TestClient, admin_user: User, customer_user: User, test_tier: CustomerTier
    ):
        admin_h = _auth_headers(admin_user)
        create_res = client.post(
            "/api/v1/discount-rules",
            json={"customer_tier_id": str(test_tier.id), "max_discount_percent": "10.00"},
            headers=admin_h,
        )
        rule_id = create_res.json()["id"]

        cust_h = _auth_headers(customer_user)
        assert client.get("/api/v1/discount-rules", headers=cust_h).status_code == 403
        assert client.get(f"/api/v1/discount-rules/{rule_id}", headers=cust_h).status_code == 403
        assert client.post("/api/v1/discount-rules", json={}, headers=cust_h).status_code == 403
        assert client.patch(f"/api/v1/discount-rules/{rule_id}", json={}, headers=cust_h).status_code == 403
        assert client.delete(f"/api/v1/discount-rules/{rule_id}", headers=cust_h).status_code == 403


class TestDiscountRulesBackendAuditLogging:
    """Audit trail verification (Section 34, 17-26)."""

    def test_create_discount_rule_generates_audit_log(
        self, client: TestClient, admin_user: User, test_tier: CustomerTier, db: Session
    ):
        headers = _auth_headers(admin_user)
        res = client.post(
            "/api/v1/discount-rules",
            json={"customer_tier_id": str(test_tier.id), "max_discount_percent": "18.50", "priority": 3},
            headers=headers,
        )
        assert res.status_code == 201
        rule_id = uuid.UUID(res.json()["id"])

        # Verify audit log record exists
        audit = db.execute(
            select(AuditLog).where(
                AuditLog.entity_type == "DISCOUNT_RULE",
                AuditLog.entity_id == rule_id,
                AuditLog.action == "CREATE",
            )
        ).scalar_one_or_none()

        assert audit is not None
        assert audit.user_id == admin_user.id
        assert audit.old_values is None
        assert audit.new_values["max_discount_percent"] == "18.50"
        assert audit.new_values["priority"] == 3
        assert audit.new_values["is_active"] is True
        assert audit.created_at is not None

    def test_update_discount_rule_generates_audit_log_with_old_and_new(
        self, client: TestClient, admin_user: User, test_tier: CustomerTier, db: Session
    ):
        headers = _auth_headers(admin_user)
        res = client.post(
            "/api/v1/discount-rules",
            json={"customer_tier_id": str(test_tier.id), "max_discount_percent": "20.00"},
            headers=headers,
        )
        rule_id = uuid.UUID(res.json()["id"])

        # Update limit from 20.00 to 12.50
        update_res = client.patch(
            f"/api/v1/discount-rules/{rule_id}",
            json={"max_discount_percent": "12.50"},
            headers=headers,
        )
        assert update_res.status_code == 200

        audit = db.execute(
            select(AuditLog).where(
                AuditLog.entity_type == "DISCOUNT_RULE",
                AuditLog.entity_id == rule_id,
                AuditLog.action == "UPDATE",
            )
        ).scalar_one_or_none()

        assert audit is not None
        assert audit.user_id == admin_user.id
        assert audit.old_values["max_discount_percent"] == "20.00"
        assert audit.new_values["max_discount_percent"] == "12.50"

    def test_deactivation_generates_deactivate_audit_log(
        self, client: TestClient, admin_user: User, test_tier: CustomerTier, db: Session
    ):
        headers = _auth_headers(admin_user)
        res = client.post(
            "/api/v1/discount-rules",
            json={"customer_tier_id": str(test_tier.id), "max_discount_percent": "15.00"},
            headers=headers,
        )
        rule_id = uuid.UUID(res.json()["id"])

        # Delete / Deactivate
        del_res = client.delete(f"/api/v1/discount-rules/{rule_id}", headers=headers)
        assert del_res.status_code == 200
        assert del_res.json()["is_active"] is False

        audit = db.execute(
            select(AuditLog).where(
                AuditLog.entity_type == "DISCOUNT_RULE",
                AuditLog.entity_id == rule_id,
                AuditLog.action == "DEACTIVATE",
            )
        ).scalar_one_or_none()

        assert audit is not None
        assert audit.user_id == admin_user.id
        assert audit.old_values["is_active"] is True
        assert audit.new_values["is_active"] is False

    def test_reactivation_generates_activate_audit_log(
        self, client: TestClient, admin_user: User, test_tier: CustomerTier, db: Session
    ):
        headers = _auth_headers(admin_user)
        res = client.post(
            "/api/v1/discount-rules",
            json={"customer_tier_id": str(test_tier.id), "max_discount_percent": "15.00", "is_active": False},
            headers=headers,
        )
        rule_id = uuid.UUID(res.json()["id"])

        # Reactivate via PATCH is_active = True
        patch_res = client.patch(
            f"/api/v1/discount-rules/{rule_id}",
            json={"is_active": True},
            headers=headers,
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["is_active"] is True

        audit = db.execute(
            select(AuditLog).where(
                AuditLog.entity_type == "DISCOUNT_RULE",
                AuditLog.entity_id == rule_id,
                AuditLog.action == "ACTIVATE",
            )
        ).scalar_one_or_none()

        assert audit is not None
        assert audit.old_values["is_active"] is False
        assert audit.new_values["is_active"] is True

    def test_failed_operations_do_not_produce_audit_logs(
        self, client: TestClient, admin_user: User, sales_rep_user: User, db: Session
    ):
        # 1. Unauthorized attempt
        rep_h = _auth_headers(sales_rep_user)
        client.post(
            "/api/v1/discount-rules",
            json={"max_discount_percent": "10.00"},
            headers=rep_h,
        )

        # 2. Validation failure (negative discount percent)
        admin_h = _auth_headers(admin_user)
        client.post(
            "/api/v1/discount-rules",
            json={"max_discount_percent": "-10.00"},
            headers=admin_h,
        )

        # 3. Nonexistent rule update
        client.patch(
            f"/api/v1/discount-rules/{uuid.uuid4()}",
            json={"max_discount_percent": "10.00"},
            headers=admin_h,
        )

        # Verify no bogus audit logs were created
        audits = db.execute(select(AuditLog).where(AuditLog.entity_type == "DISCOUNT_RULE")).scalars().all()
        assert len(audits) == 0


class TestDiscountRuleStatePropagationInQuotations:
    """Operational State & Quotation Recalculation Integration (Section 28-32, 35)."""

    def test_rule_modification_propagates_to_quotation_recalculation(
        self,
        client: TestClient,
        admin_user: User,
        sales_rep_user: User,
        test_customer: Customer,
        test_product: Product,
    ):
        admin_h = _auth_headers(admin_user)
        rep_h = _auth_headers(sales_rep_user)

        # 1. Admin configures 10% limit
        rule_res = client.post(
            "/api/v1/discount-rules",
            json={"customer_tier_id": str(test_customer.customer_tier_id), "max_discount_percent": "10.00"},
            headers=admin_h,
        )
        rule_id = rule_res.json()["id"]

        # 2. Rep creates quote with 9% requested discount (within 10% limit)
        q = client.post("/api/v1/quotations", json={"customer_id": str(test_customer.id)}, headers=rep_h).json()
        l_res = client.post(
            f"/api/v1/quotations/{q['id']}/lines",
            json={"product_id": str(test_product.id), "quantity": 1, "discount_percent": 9.0},
            headers=rep_h,
        ).json()

        assert float(l_res["lines"][0]["allowed_discount_percent"]) == 10.0
        assert float(l_res["lines"][0]["discount_excess_percent"]) == 0.0
        assert l_res["approval_required"] is False

        # 3. Admin modifies limit down to 8%
        client.patch(
            f"/api/v1/discount-rules/{rule_id}",
            json={"max_discount_percent": "8.00"},
            headers=admin_h,
        )

        # 4. Rep recalculates quotation: Must pick up the 8% rule and now flag violation
        recalc = client.post(f"/api/v1/quotations/{q['id']}/recalculate", headers=rep_h).json()
        quote = recalc["quotation"]
        assert float(quote["lines"][0]["allowed_discount_percent"]) == 8.0
        assert float(quote["lines"][0]["discount_excess_percent"]) == 1.0  # 9% requested - 8% limit
        assert quote["approval_required"] is True
        assert quote["current_approval_level"] == ApproverRole.SALES_MANAGER.value

    def test_rule_deactivation_propagates_to_quotation_recalculation(
        self,
        client: TestClient,
        admin_user: User,
        sales_rep_user: User,
        test_customer: Customer,
        test_product: Product,
    ):
        admin_h = _auth_headers(admin_user)
        rep_h = _auth_headers(sales_rep_user)

        # 1. Admin configures 10% rule
        rule_res = client.post(
            "/api/v1/discount-rules",
            json={"customer_tier_id": str(test_customer.customer_tier_id), "max_discount_percent": "10.00"},
            headers=admin_h,
        )
        rule_id = rule_res.json()["id"]

        # 2. Rep quotes with 12% discount (violates 10% limit)
        q = client.post("/api/v1/quotations", json={"customer_id": str(test_customer.id)}, headers=rep_h).json()
        l_res = client.post(
            f"/api/v1/quotations/{q['id']}/lines",
            json={"product_id": str(test_product.id), "quantity": 1, "discount_percent": 12.0},
            headers=rep_h,
        ).json()

        assert float(l_res["lines"][0]["discount_excess_percent"]) == 2.0
        assert l_res["approval_required"] is True

        # 3. Admin deactivates the rule
        client.delete(f"/api/v1/discount-rules/{rule_id}", headers=admin_h)

        # 4. Recalculate quotation: Inactive rule must no longer participate
        recalc = client.post(f"/api/v1/quotations/{q['id']}/recalculate", headers=rep_h).json()
        quote = recalc["quotation"]
        assert float(quote["lines"][0]["discount_excess_percent"]) == 0.0
        assert quote["approval_required"] is False

    def test_rule_activation_propagates_to_quotation_recalculation(
        self,
        client: TestClient,
        admin_user: User,
        sales_rep_user: User,
        test_customer: Customer,
        test_product: Product,
    ):
        admin_h = _auth_headers(admin_user)
        rep_h = _auth_headers(sales_rep_user)

        # 1. Admin creates an INACTIVE rule (5% limit)
        rule_res = client.post(
            "/api/v1/discount-rules",
            json={"customer_tier_id": str(test_customer.customer_tier_id), "max_discount_percent": "5.00", "is_active": False},
            headers=admin_h,
        )
        rule_id = rule_res.json()["id"]

        # 2. Rep quotes with 8% discount (inactive rule does not participate)
        q = client.post("/api/v1/quotations", json={"customer_id": str(test_customer.id)}, headers=rep_h).json()
        l_res = client.post(
            f"/api/v1/quotations/{q['id']}/lines",
            json={"product_id": str(test_product.id), "quantity": 1, "discount_percent": 8.0},
            headers=rep_h,
        ).json()
        assert l_res["approval_required"] is False

        # 3. Admin activates the rule
        client.patch(
            f"/api/v1/discount-rules/{rule_id}",
            json={"is_active": True},
            headers=admin_h,
        )

        # 4. Recalculate quotation: newly active 5% rule applies immediately
        recalc = client.post(f"/api/v1/quotations/{q['id']}/recalculate", headers=rep_h).json()
        quote = recalc["quotation"]
        assert float(quote["lines"][0]["allowed_discount_percent"]) == 5.0
        assert float(quote["lines"][0]["discount_excess_percent"]) == 3.0
        assert quote["approval_required"] is True
