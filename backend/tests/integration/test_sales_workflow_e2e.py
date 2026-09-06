"""Comprehensive End-to-End Sales Workflow Integration Test.

Validates the complete cohesive lifecycle:
Quotation (Draft) → Pricing → Discount/Risk → Submit (Auto-Routing) → Sequential Approvals (Manager -> Finance) → Send → Confirmation → Order Creation
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import (
    ApprovalStatus,
    ApproverRole,
    OrderStatus,
    QuotationStatus,
    UserRole,
)
from app.core.security import create_access_token, hash_password
from app.models.approval_policy import ApprovalPolicy
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.discount_rule import DiscountRule
from app.models.price_list import PriceList
from app.models.price_list_item import PriceListItem
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.user import User


def _auth_headers(user: User) -> dict:
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sales_rep(db: Session) -> User:
    user = User(
        name="Alice Rep",
        email=f"alice-{uuid.uuid4().hex[:6]}@dealflow.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.SALES_REP,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sales_manager(db: Session) -> User:
    user = User(
        name="Bob Manager",
        email=f"bob-{uuid.uuid4().hex[:6]}@dealflow.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.SALES_MANAGER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def finance_ops(db: Session) -> User:
    user = User(
        name="Carol Finance",
        email=f"carol-{uuid.uuid4().hex[:6]}@dealflow.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.FINANCE_OPERATIONS,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def commercial_environment(db: Session) -> dict:
    # 1. Customer Tier
    tier = CustomerTier(
        name=f"Enterprise Tier {uuid.uuid4().hex[:4]}",
        default_discount_limit=Decimal("15.00"),
        is_active=True,
    )
    db.add(tier)
    db.flush()

    # 2. Customer
    customer = Customer(
        name="Acme Global Corporation",
        email=f"procurement-{uuid.uuid4().hex[:6]}@acmeglobal.com",
        customer_tier_id=tier.id,
        is_active=True,
    )
    db.add(customer)
    db.flush()

    # 3. Product Category
    hardware_cat = ProductCategory(name=f"Hardware {uuid.uuid4().hex[:4]}", is_active=True)
    db.add(hardware_cat)
    db.flush()

    # 4. Product
    server_prod = Product(
        sku=f"SERVER-{uuid.uuid4().hex[:6]}",
        name="Enterprise Rack Server",
        unit="PCS",
        base_price=Decimal("5000.00"),
        cost_price=Decimal("3000.00"),
        tax_rate=Decimal("8.00"),
        category_id=hardware_cat.id,
        is_active=True,
    )
    db.add(server_prod)
    db.flush()

    # 5. Price List with tier-specific price ($4800 instead of $5000)
    price_list = PriceList(
        name=f"Enterprise Price List {uuid.uuid4().hex[:4]}",
        customer_tier_id=tier.id,
        currency="USD",
        is_active=True,
    )
    db.add(price_list)
    db.flush()

    db.add(
        PriceListItem(
            price_list_id=price_list.id,
            product_id=server_prod.id,
            price=Decimal("4800.00"),
        )
    )

    # 6. Discount Governance Rule: Max 12% for this Tier
    db.add(
        DiscountRule(
            customer_tier_id=tier.id,
            max_discount_percent=Decimal("12.00"),
            priority=10,
            is_active=True,
        )
    )

    # 7. Approval Policies:
    # Policy A: Low risk (<= 10.00) -> Manager only
    db.add(
        ApprovalPolicy(
            name="Sales Manager Boundary",
            min_risk_score=Decimal("1.00"),
            max_risk_score=Decimal("10.00"),
            requires_manager=True,
            requires_finance=False,
            priority=1,
            is_active=True,
        )
    )
    # Policy B: High risk (> 10.00) -> Manager + Finance
    db.add(
        ApprovalPolicy(
            name="Executive Finance Boundary",
            min_risk_score=Decimal("10.01"),
            max_risk_score=None,
            requires_manager=True,
            requires_finance=True,
            priority=5,
            is_active=True,
        )
    )

    db.commit()

    return {
        "tier": tier,
        "customer": customer,
        "product": server_prod,
    }


class TestSalesWorkflowE2E:
    """Multi-actor full lifecycle integration test."""

    def test_complete_sales_workflow_journey(
        self,
        client: TestClient,
        commercial_environment: dict,
        sales_rep: User,
        sales_manager: User,
        finance_ops: User,
    ):
        env = commercial_environment
        customer = env["customer"]
        product = env["product"]

        rep_headers = _auth_headers(sales_rep)
        mgr_headers = _auth_headers(sales_manager)
        fin_headers = _auth_headers(finance_ops)

        # -------------------------------------------------------------
        # STEP 1: Sales Rep creates Draft Quotation
        # -------------------------------------------------------------
        create_res = client.post(
            "/api/v1/quotations",
            json={"customer_id": str(customer.id)},
            headers=rep_headers,
        )
        assert create_res.status_code == 201
        quote = create_res.json()
        quote_id = quote["id"]
        assert quote["status"] == QuotationStatus.DRAFT.value
        assert quote["customer_id"] == str(customer.id)
        assert quote["quotation_number"].startswith("QT-")

        # -------------------------------------------------------------
        # STEP 2: Add Line & Validate Authoritative Pricing Resolution
        # -------------------------------------------------------------
        # Customer tier price list resolved unit price ($4800)
        # Sales Rep requests 25% discount (exceeds 12% ceiling by 13%!)
        line_res = client.post(
            f"/api/v1/quotations/{quote_id}/lines",
            json={
                "product_id": str(product.id),
                "quantity": 2,
                "discount_percent": 25.0,
                "tax_rate": 8.0,
            },
            headers=rep_headers,
        )
        assert line_res.status_code == 201
        quote_with_lines = line_res.json()
        assert len(quote_with_lines["lines"]) == 1
        line = quote_with_lines["lines"][0]

        # Verify pricing engine resolved price list price $4800
        assert float(line["unit_price"]) == 4800.0
        # Verify discount ceiling snapshot
        assert float(line["allowed_discount_percent"]) == 12.0
        assert float(line["discount_excess_percent"]) == 13.0
        # Financials
        assert float(line["discount_amount"]) == 2400.0  # 2 * 4800 * 0.25
        # Risk evaluation: 13% excess -> risk score = 26.00 -> triggers Manager + Finance approval
        assert float(quote_with_lines["risk_score"]) == 26.0
        assert quote_with_lines["approval_required"] is True
        assert quote_with_lines["current_approval_level"] == ApproverRole.FINANCE_OPERATIONS.value

        # -------------------------------------------------------------
        # STEP 3: Submit Quotation -> Auto-routing to Approval Workflow
        # -------------------------------------------------------------
        submit_res = client.post(f"/api/v1/quotations/{quote_id}/submit", headers=rep_headers)
        assert submit_res.status_code == 200
        submitted_quote = submit_res.json()
        assert submitted_quote["status"] == QuotationStatus.PENDING_APPROVAL.value

        # Verify Approval Instance created for quotation
        approvals_res = client.get(f"/api/v1/quotations/{quote_id}/approvals", headers=rep_headers)
        assert approvals_res.status_code == 200
        approvals = approvals_res.json()
        assert len(approvals) == 1
        approval_instance = approvals[0]
        inst_id = approval_instance["id"]
        assert approval_instance["status"] == ApprovalStatus.PENDING.value
        assert len(approval_instance["steps"]) == 2

        step1 = approval_instance["steps"][0]
        assert step1["step_order"] == 1
        assert step1["approver_role"] == ApproverRole.SALES_MANAGER.value
        assert step1["status"] == ApprovalStatus.PENDING.value

        step2 = approval_instance["steps"][1]
        assert step2["step_order"] == 2
        assert step2["approver_role"] == ApproverRole.FINANCE_OPERATIONS.value
        assert step2["status"] == ApprovalStatus.PENDING.value

        # -------------------------------------------------------------
        # STEP 4: Sequential Approval - Sales Manager reviews and approves
        # -------------------------------------------------------------
        # Finance cannot approve before manager
        fin_early_res = client.post(
            f"/api/v1/approvals/{inst_id}/approve",
            json={"reason": "Premature finance approval"},
            headers=fin_headers,
        )
        assert fin_early_res.status_code in (400, 403)

        # Manager approves step 1
        mgr_approve_res = client.post(
            f"/api/v1/approvals/{inst_id}/approve",
            json={"reason": "Strategic enterprise account, approved by sales management"},
            headers=mgr_headers,
        )
        assert mgr_approve_res.status_code == 200
        inst_after_mgr = mgr_approve_res.json()
        assert inst_after_mgr["status"] == ApprovalStatus.PENDING.value
        assert inst_after_mgr["steps"][0]["status"] == ApprovalStatus.APPROVED.value
        assert inst_after_mgr["steps"][1]["status"] == ApprovalStatus.PENDING.value

        # Quotation is still PENDING_APPROVAL until Finance completes
        q_mid = client.get(f"/api/v1/quotations/{quote_id}", headers=rep_headers).json()
        assert q_mid["status"] == QuotationStatus.PENDING_APPROVAL.value

        # -------------------------------------------------------------
        # STEP 5: Finance Operations reviews and approves (Final Step)
        # -------------------------------------------------------------
        fin_approve_res = client.post(
            f"/api/v1/approvals/{inst_id}/approve",
            json={"reason": "Gross margin remains above 30%, approved by finance operations"},
            headers=fin_headers,
        )
        assert fin_approve_res.status_code == 200
        inst_after_fin = fin_approve_res.json()
        assert inst_after_fin["status"] == ApprovalStatus.APPROVED.value
        assert inst_after_fin["steps"][1]["status"] == ApprovalStatus.APPROVED.value
        assert inst_after_fin["completed_at"] is not None

        # Quotation is now APPROVED!
        q_approved = client.get(f"/api/v1/quotations/{quote_id}", headers=rep_headers).json()
        assert q_approved["status"] == QuotationStatus.APPROVED.value

        # -------------------------------------------------------------
        # STEP 6: Send Quotation to Customer
        # -------------------------------------------------------------
        send_res = client.post(f"/api/v1/quotations/{quote_id}/send", headers=rep_headers)
        assert send_res.status_code == 200
        sent_quote = send_res.json()
        assert sent_quote["status"] == QuotationStatus.SENT.value
        assert sent_quote["sent_at"] is not None

        # -------------------------------------------------------------
        # STEP 7: Confirm Quotation & Generate Order
        # -------------------------------------------------------------
        confirm_res = client.post(f"/api/v1/quotations/{quote_id}/confirm", headers=rep_headers)
        assert confirm_res.status_code == 200
        conf_data = confirm_res.json()

        assert conf_data["quotation"]["status"] == QuotationStatus.CONFIRMED.value
        order = conf_data["order"]
        assert order["quotation_id"] == quote_id
        assert order["status"] == OrderStatus.CONFIRMED.value
        assert order["order_number"].startswith("SO-")
        assert float(order["total_amount"]) > 0

        # Verify order retrieval via quotation
        q_order = client.get(f"/api/v1/quotations/{quote_id}/order", headers=rep_headers).json()
        assert q_order["id"] == order["id"]

        # -------------------------------------------------------------
        # STEP 8: Check Pipeline & Audit Trails
        # -------------------------------------------------------------
        pipeline_res = client.get("/api/v1/pipeline", headers=rep_headers).json()
        confirmed_stage = next(s for s in pipeline_res["stages"] if s["stage"] == QuotationStatus.CONFIRMED.value)
        assert any(c["quotation_id"] == quote_id for c in confirmed_stage["cards"])

        # Quotation Audit Trail
        q_audit = client.get(f"/api/v1/quotations/{quote_id}/audit-log", headers=rep_headers).json()
        q_actions = [a["action"] for a in q_audit]
        assert "CREATE" in q_actions
        assert "ADD_LINE" in q_actions
        assert "SUBMIT" in q_actions
        assert "SEND" in q_actions
        assert "CONFIRM" in q_actions

        # Order Audit Trail
        o_audit = client.get(f"/api/v1/orders/{order['id']}/audit-log", headers=rep_headers).json()
        assert len(o_audit) >= 1
        assert o_audit[0]["action"] == "CREATE"
