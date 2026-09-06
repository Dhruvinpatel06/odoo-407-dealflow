"""API tests for Quotation Confirmation, Orders, and Pipeline endpoints."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import OrderStatus, QuotationStatus, UserRole
from app.core.security import create_access_token, hash_password
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.discount_rule import DiscountRule
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.user import User


def _create_auth_headers(user: User) -> dict:
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
def test_setup(db: Session, sales_rep_user: User) -> dict:
    tier = CustomerTier(
        name=f"Gold-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("20.00"),
        is_active=True,
    )
    db.add(tier)
    db.flush()

    customer = Customer(
        name="Global Tech Ltd",
        email=f"client-{uuid.uuid4().hex[:6]}@global.com",
        customer_tier_id=tier.id,
        is_active=True,
    )
    db.add(customer)
    db.flush()

    cat = ProductCategory(name=f"Electronics-{uuid.uuid4().hex[:6]}", is_active=True)
    db.add(cat)
    db.flush()

    prod = Product(
        sku=f"MONITOR-{uuid.uuid4().hex[:6]}",
        name="4K Monitor",
        unit="PCS",
        base_price=Decimal("500.00"),
        cost_price=Decimal("300.00"),
        tax_rate=Decimal("10.00"),
        category_id=cat.id,
        is_active=True,
    )
    db.add(prod)

    # 20% discount rule
    db.add(
        DiscountRule(
            customer_tier_id=tier.id,
            max_discount_percent=Decimal("20.00"),
            priority=1,
            is_active=True,
        )
    )
    db.commit()

    return {
        "customer": customer,
        "product": prod,
        "sales_rep": sales_rep_user,
    }


class TestQuotationConfirmationAndOrdersAPI:
    """Tests covering Quotation confirmation, Order creation, and Pipeline."""

    def test_confirm_quotation_success_and_creates_order(
        self, client: TestClient, test_setup: dict, sales_rep_user: User
    ):
        data = test_setup
        headers = _create_auth_headers(sales_rep_user)

        # 1. Create quotation & add line with 10% discount (allowed under 20% rule -> no approval required)
        q_res = client.post(
            "/api/v1/quotations",
            json={"customer_id": str(data["customer"].id)},
            headers=headers,
        ).json()
        q_id = q_res["id"]

        client.post(
            f"/api/v1/quotations/{q_id}/lines",
            json={"product_id": str(data["product"].id), "quantity": 2, "discount_percent": 10.0},
            headers=headers,
        )

        # 2. Submit -> automatically APPROVED because discount is within limit
        submit_res = client.post(f"/api/v1/quotations/{q_id}/submit", headers=headers).json()
        assert submit_res["status"] == QuotationStatus.APPROVED.value

        # 3. Confirm quotation
        confirm_res = client.post(f"/api/v1/quotations/{q_id}/confirm", headers=headers)
        assert confirm_res.status_code == 200
        c_data = confirm_res.json()

        assert c_data["quotation"]["status"] == QuotationStatus.CONFIRMED.value
        assert "order" in c_data
        order = c_data["order"]
        assert order["quotation_id"] == q_id
        assert order["status"] == OrderStatus.CONFIRMED.value
        assert order["order_number"].startswith("SO-")
        assert float(order["total_amount"]) > 0

        # 4. Fetch order via GET /api/v1/quotations/{id}/order
        q_order = client.get(f"/api/v1/quotations/{q_id}/order", headers=headers)
        assert q_order.status_code == 200
        assert q_order.json()["id"] == order["id"]

        # 5. Fetch order via GET /api/v1/orders/{id}
        direct_order = client.get(f"/api/v1/orders/{order['id']}", headers=headers)
        assert direct_order.status_code == 200
        assert direct_order.json()["order_number"] == order["order_number"]

        # 6. List orders via GET /api/v1/orders
        orders_list = client.get("/api/v1/orders", headers=headers)
        assert orders_list.status_code == 200
        assert any(o["id"] == order["id"] for o in orders_list.json())

        # 7. Verify order audit log
        order_audit = client.get(f"/api/v1/orders/{order['id']}/audit-log", headers=headers)
        assert order_audit.status_code == 200
        assert len(order_audit.json()) >= 1
        assert order_audit.json()[0]["action"] == "CREATE"

    def test_duplicate_confirmation_prevented(
        self, client: TestClient, test_setup: dict, sales_rep_user: User
    ):
        data = test_setup
        headers = _create_auth_headers(sales_rep_user)

        q_res = client.post(
            "/api/v1/quotations",
            json={"customer_id": str(data["customer"].id)},
            headers=headers,
        ).json()
        q_id = q_res["id"]
        client.post(
            f"/api/v1/quotations/{q_id}/lines",
            json={"product_id": str(data["product"].id), "quantity": 1, "discount_percent": 5.0},
            headers=headers,
        )
        client.post(f"/api/v1/quotations/{q_id}/submit", headers=headers)

        # First confirm: OK
        res1 = client.post(f"/api/v1/quotations/{q_id}/confirm", headers=headers)
        assert res1.status_code == 200

        # Second confirm: Must fail (idempotent / duplicate protection)
        res2 = client.post(f"/api/v1/quotations/{q_id}/confirm", headers=headers)
        assert res2.status_code == 400
        assert "already" in res2.json()["detail"].lower()

    def test_cannot_confirm_draft_or_unapproved_quotation(
        self, client: TestClient, test_setup: dict, sales_rep_user: User
    ):
        data = test_setup
        headers = _create_auth_headers(sales_rep_user)

        # 1. Quotation in DRAFT cannot be confirmed
        q_res = client.post(
            "/api/v1/quotations",
            json={"customer_id": str(data["customer"].id)},
            headers=headers,
        ).json()
        q_id = q_res["id"]
        client.post(
            f"/api/v1/quotations/{q_id}/lines",
            json={"product_id": str(data["product"].id), "quantity": 1},
            headers=headers,
        )

        draft_confirm = client.post(f"/api/v1/quotations/{q_id}/confirm", headers=headers)
        assert draft_confirm.status_code == 400

    def test_delete_quotation_draft_vs_confirmed(
        self, client: TestClient, test_setup: dict, sales_rep_user: User
    ):
        data = test_setup
        headers = _create_auth_headers(sales_rep_user)

        # 1. DRAFT quotation can be deleted
        q_res = client.post(
            "/api/v1/quotations",
            json={"customer_id": str(data["customer"].id)},
            headers=headers,
        ).json()
        del_res = client.delete(f"/api/v1/quotations/{q_res['id']}", headers=headers)
        assert del_res.status_code == 200

        # Verify it's gone
        get_res = client.get(f"/api/v1/quotations/{q_res['id']}", headers=headers)
        assert get_res.status_code == 404

    def test_sales_pipeline_endpoint(
        self, client: TestClient, test_setup: dict, sales_rep_user: User
    ):
        data = test_setup
        headers = _create_auth_headers(sales_rep_user)

        # Create quote
        client.post(
            "/api/v1/quotations",
            json={"customer_id": str(data["customer"].id)},
            headers=headers,
        )

        res = client.get("/api/v1/pipeline", headers=headers)
        assert res.status_code == 200
        p_data = res.json()
        assert "stages" in p_data
        assert "total_deals" in p_data
        assert "total_pipeline_value" in p_data
        stage_names = [s["stage"] for s in p_data["stages"]]
        assert QuotationStatus.DRAFT.value in stage_names
        assert QuotationStatus.CONFIRMED.value in stage_names
