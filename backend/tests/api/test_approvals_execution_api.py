"""API tests for Approval Execution endpoints."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import ApprovalStatus, ApproverRole, QuotationStatus, UserRole
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
def sales_manager_user(db: Session) -> User:
    user = User(
        name="Sales Manager",
        email=f"mgr-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.SALES_MANAGER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def finance_user(db: Session) -> User:
    user = User(
        name="Finance Ops",
        email=f"fin-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.FINANCE_OPERATIONS,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db: Session) -> User:
    user = User(
        name="Admin",
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
def setup_submitted_quote_two_steps(
    db: Session,
    sales_rep_user: User,
) -> tuple[dict, str]:
    """Helper fixture creating a submitted quotation requiring 2-stage approval (Manager + Finance)."""
    tier = CustomerTier(
        name=f"Tier-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("10.00"),
        is_active=True,
    )
    db.add(tier)
    db.flush()

    customer = Customer(
        name="Test Corp",
        email=f"test-{uuid.uuid4().hex[:6]}@corp.com",
        customer_tier_id=tier.id,
        is_active=True,
    )
    db.add(customer)
    db.flush()

    cat = ProductCategory(name=f"Cat-{uuid.uuid4().hex[:6]}", is_active=True)
    db.add(cat)
    db.flush()

    prod = Product(
        sku=f"SKU-{uuid.uuid4().hex[:6]}",
        name="Enterprise Server",
        unit="PCS",
        base_price=Decimal("2000.00"),
        cost_price=Decimal("1200.00"),
        tax_rate=Decimal("0.00"),
        category_id=cat.id,
        is_active=True,
    )
    db.add(prod)
    db.flush()

    # Rule: max 10%
    db.add(
        DiscountRule(
            customer_tier_id=tier.id,
            max_discount_percent=Decimal("10.00"),
            priority=1,
            is_active=True,
        )
    )
    # Policy requiring Finance (risk > 10.00)
    db.add(
        ApprovalPolicy(
            name="Finance Policy",
            min_risk_score=Decimal("10.01"),
            max_risk_score=None,
            requires_manager=True,
            requires_finance=True,
            priority=10,
            is_active=True,
        )
    )
    db.commit()

    return {
        "customer": customer,
        "product": prod,
        "sales_rep": sales_rep_user,
    }


class TestApprovalExecutionAPI:
    """Tests covering approval execution endpoints and sequential rules."""

    def test_list_approvals_and_pending(
        self,
        client: TestClient,
        setup_submitted_quote_two_steps: dict,
        sales_manager_user: User,
        finance_user: User,
        sales_rep_user: User,
    ):
        data = setup_submitted_quote_two_steps
        rep_headers = _create_auth_headers(sales_rep_user)

        # 1. Create quotation & line with 25% discount (exceeds 10% by 15% -> risk = 30.00 -> 2 steps)
        q_res = client.post(
            "/api/v1/quotations",
            json={"customer_id": str(data["customer"].id)},
            headers=rep_headers,
        ).json()
        client.post(
            f"/api/v1/quotations/{q_res['id']}/lines",
            json={"product_id": str(data["product"].id), "quantity": 1, "discount_percent": 25.0},
            headers=rep_headers,
        )
        submit_res = client.post(f"/api/v1/quotations/{q_res['id']}/submit", headers=rep_headers).json()
        assert submit_res["status"] == QuotationStatus.PENDING_APPROVAL.value

        # 2. List approvals (Manager)
        mgr_headers = _create_auth_headers(sales_manager_user)
        list_res = client.get("/api/v1/approvals", headers=mgr_headers)
        assert list_res.status_code == 200
        instances = list_res.json()
        assert len(instances) >= 1
        inst = next(i for i in instances if i["quotation_id"] == q_res["id"])
        assert inst["status"] == ApprovalStatus.PENDING.value
        assert len(inst["steps"]) == 2
        assert inst["steps"][0]["step_order"] == 1
        assert inst["steps"][0]["approver_role"] == ApproverRole.SALES_MANAGER.value
        assert inst["steps"][1]["step_order"] == 2
        assert inst["steps"][1]["approver_role"] == ApproverRole.FINANCE_OPERATIONS.value

        # 3. Check /approvals/pending for Sales Manager (step 1 is actionable)
        mgr_pending = client.get("/api/v1/approvals/pending", headers=mgr_headers).json()
        assert any(p["approval_instance_id"] == inst["id"] and p["step_order"] == 1 for p in mgr_pending)

        # 4. Check /approvals/pending for Finance Ops (step 2 is NOT actionable until step 1 is approved!)
        fin_headers = _create_auth_headers(finance_user)
        fin_pending = client.get("/api/v1/approvals/pending", headers=fin_headers).json()
        assert not any(p["approval_instance_id"] == inst["id"] for p in fin_pending)

    def test_sequential_approval_execution_success(
        self,
        client: TestClient,
        setup_submitted_quote_two_steps: dict,
        sales_manager_user: User,
        finance_user: User,
        sales_rep_user: User,
    ):
        data = setup_submitted_quote_two_steps
        rep_headers = _create_auth_headers(sales_rep_user)

        q_res = client.post(
            "/api/v1/quotations",
            json={"customer_id": str(data["customer"].id)},
            headers=rep_headers,
        ).json()
        client.post(
            f"/api/v1/quotations/{q_res['id']}/lines",
            json={"product_id": str(data["product"].id), "quantity": 1, "discount_percent": 25.0},
            headers=rep_headers,
        )
        client.post(f"/api/v1/quotations/{q_res['id']}/submit", headers=rep_headers)

        mgr_headers = _create_auth_headers(sales_manager_user)
        fin_headers = _create_auth_headers(finance_user)

        instances = client.get("/api/v1/approvals", headers=mgr_headers).json()
        inst = next(i for i in instances if i["quotation_id"] == q_res["id"])
        inst_id = inst["id"]

        # 1. Finance attempts to approve step 2 before Manager approves -> Forbidden/Rejected
        fin_fail = client.post(
            f"/api/v1/approvals/{inst_id}/approve",
            json={"reason": "Finance pre-approval attempt"},
            headers=fin_headers,
        )
        # Cannot act on step 1 (requires SALES_MANAGER)
        assert fin_fail.status_code in (400, 403)

        # 2. Sales Rep attempts to approve -> Forbidden (403)
        rep_fail = client.post(
            f"/api/v1/approvals/{inst_id}/approve",
            json={"reason": "Self-approval attempt"},
            headers=rep_headers,
        )
        assert rep_fail.status_code == 403

        # 3. Manager approves Step 1
        mgr_app = client.post(
            f"/api/v1/approvals/{inst_id}/approve",
            json={"reason": "Looks good from sales perspective"},
            headers=mgr_headers,
        )
        assert mgr_app.status_code == 200
        inst_after_mgr = mgr_app.json()
        assert inst_after_mgr["status"] == ApprovalStatus.PENDING.value
        assert inst_after_mgr["steps"][0]["status"] == ApprovalStatus.APPROVED.value
        assert inst_after_mgr["steps"][0]["decision_reason"] == "Looks good from sales perspective"
        assert inst_after_mgr["steps"][1]["status"] == ApprovalStatus.PENDING.value

        # Quotation is still PENDING_APPROVAL because step 2 (Finance) is pending
        q_check = client.get(f"/api/v1/quotations/{q_res['id']}", headers=rep_headers).json()
        assert q_check["status"] == QuotationStatus.PENDING_APPROVAL.value

        # 4. Now Finance sees it in /approvals/pending
        fin_pending = client.get("/api/v1/approvals/pending", headers=fin_headers).json()
        assert any(p["approval_instance_id"] == inst_id and p["step_order"] == 2 for p in fin_pending)

        # 5. Finance approves Step 2 (Final Step)
        fin_app = client.post(
            f"/api/v1/approvals/{inst_id}/approve",
            json={"reason": "Margin acceptable for Q3"},
            headers=fin_headers,
        )
        assert fin_app.status_code == 200
        inst_final = fin_app.json()
        assert inst_final["status"] == ApprovalStatus.APPROVED.value
        assert inst_final["completed_at"] is not None

        # Quotation is now APPROVED!
        q_final = client.get(f"/api/v1/quotations/{q_res['id']}", headers=rep_headers).json()
        assert q_final["status"] == QuotationStatus.APPROVED.value

        # 6. Verify audit log endpoint for approval
        audit_res = client.get(f"/api/v1/approvals/{inst_id}/audit-log", headers=mgr_headers)
        assert audit_res.status_code == 200
        logs = audit_res.json()
        assert len(logs) >= 2
        actions = [l["action"] for l in logs]
        assert "APPROVE" in actions

    def test_rejection_workflow(
        self,
        client: TestClient,
        setup_submitted_quote_two_steps: dict,
        sales_manager_user: User,
        sales_rep_user: User,
    ):
        data = setup_submitted_quote_two_steps
        rep_headers = _create_auth_headers(sales_rep_user)

        q_res = client.post(
            "/api/v1/quotations",
            json={"customer_id": str(data["customer"].id)},
            headers=rep_headers,
        ).json()
        client.post(
            f"/api/v1/quotations/{q_res['id']}/lines",
            json={"product_id": str(data["product"].id), "quantity": 1, "discount_percent": 25.0},
            headers=rep_headers,
        )
        client.post(f"/api/v1/quotations/{q_res['id']}/submit", headers=rep_headers)

        mgr_headers = _create_auth_headers(sales_manager_user)
        instances = client.get("/api/v1/approvals", headers=mgr_headers).json()
        inst = next(i for i in instances if i["quotation_id"] == q_res["id"])

        # Manager rejects
        rej_res = client.post(
            f"/api/v1/approvals/{inst['id']}/reject",
            json={"reason": "Discount is too deep for new account"},
            headers=mgr_headers,
        )
        assert rej_res.status_code == 200
        rej_data = rej_res.json()
        assert rej_data["status"] == ApprovalStatus.REJECTED.value

        # Quotation is now REJECTED
        q_after = client.get(f"/api/v1/quotations/{q_res['id']}", headers=rep_headers).json()
        assert q_after["status"] == QuotationStatus.REJECTED.value

    def test_return_for_revision_workflow(
        self,
        client: TestClient,
        setup_submitted_quote_two_steps: dict,
        sales_manager_user: User,
        sales_rep_user: User,
    ):
        data = setup_submitted_quote_two_steps
        rep_headers = _create_auth_headers(sales_rep_user)

        q_res = client.post(
            "/api/v1/quotations",
            json={"customer_id": str(data["customer"].id)},
            headers=rep_headers,
        ).json()
        client.post(
            f"/api/v1/quotations/{q_res['id']}/lines",
            json={"product_id": str(data["product"].id), "quantity": 1, "discount_percent": 25.0},
            headers=rep_headers,
        )
        client.post(f"/api/v1/quotations/{q_res['id']}/submit", headers=rep_headers)

        mgr_headers = _create_auth_headers(sales_manager_user)
        instances = client.get("/api/v1/approvals", headers=mgr_headers).json()
        inst = next(i for i in instances if i["quotation_id"] == q_res["id"])

        # Manager returns for revision
        rev_res = client.post(
            f"/api/v1/approvals/{inst['id']}/return-for-revision",
            json={"reason": "Lower discount to 15% and resubmit"},
            headers=mgr_headers,
        )
        assert rev_res.status_code == 200
        rev_data = rev_res.json()
        assert rev_data["status"] == ApprovalStatus.REVISION_REQUIRED.value

        # Quotation is now REVISION_REQUIRED
        q_after = client.get(f"/api/v1/quotations/{q_res['id']}", headers=rep_headers).json()
        assert q_after["status"] == QuotationStatus.REVISION_REQUIRED.value
