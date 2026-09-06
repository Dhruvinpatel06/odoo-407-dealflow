"""API tests for Subscription Plans and Subscriptions endpoints."""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import (
    BillingInterval,
    OrderStatus,
    ProrationMethod,
    QuotationStatus,
    SubscriptionStatus,
    UserRole,
)
from app.core.security import create_access_token, hash_password
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.order import Order
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuotationLine
from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User


def _auth(user: User) -> dict:
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def finance_user(db: Session) -> User:
    user = User(
        name="Finance Manager",
        email=f"fin-sub-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Pass123!"),
        role=UserRole.FINANCE_OPERATIONS,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sales_rep_user(db: Session) -> User:
    user = User(
        name="Sales Rep",
        email=f"rep-sub-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Pass123!"),
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
        name="Portal Customer",
        email=f"cust-sub-{uuid.uuid4().hex[:6]}@client.com",
        password_hash=hash_password("Pass123!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def subscription_setup(db: Session, sales_rep_user: User) -> dict:
    tier = CustomerTier(
        name=f"Tier-Sub-{uuid.uuid4().hex[:4]}",
        default_discount_limit=Decimal("20.00"),
        is_active=True,
    )
    db.add(tier)
    db.flush()

    customer = Customer(
        name="SaaS Enterprise Client",
        customer_tier_id=tier.id,
        is_active=True,
    )
    db.add(customer)
    db.flush()

    cat = ProductCategory(
        name=f"SaaS Category-{uuid.uuid4().hex[:4]}",
        is_active=True,
    )
    db.add(cat)
    db.flush()

    prod = Product(
        name="Cloud Monitoring Suite",
        sku=f"SaaS-{uuid.uuid4().hex[:6].upper()}",
        category_id=cat.id,
        unit="SEAT",
        base_price=Decimal("100.00"),
        cost_price=Decimal("20.00"),
        tax_rate=Decimal("0.00"),
        is_subscription=True,
        is_active=True,
    )
    db.add(prod)
    db.flush()

    plan = SubscriptionPlan(
        name="Pro Monthly",
        billing_interval=BillingInterval.MONTHLY,
        interval_count=1,
        proration_method=ProrationMethod.DAILY_PRO_RATA,
        cancellation_policy="IMMEDIATE",
        refund_policy="PRO_RATA",
        is_active=True,
    )
    db.add(plan)
    db.flush()

    quote = Quotation(
        quotation_number=f"QT-SUB-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer.id,
        sales_rep_id=sales_rep_user.id,
        status=QuotationStatus.CONFIRMED,
        subtotal=Decimal("500.00"),
        total_amount=Decimal("500.00"),
    )
    db.add(quote)
    db.flush()

    qline = QuotationLine(
        quotation_id=quote.id,
        product_id=prod.id,
        quantity=Decimal("5.00"),
        unit_price=Decimal("100.00"),
        line_total=Decimal("500.00"),
    )
    db.add(qline)
    db.flush()

    order = Order(
        order_number=f"SO-SUB-{uuid.uuid4().hex[:6].upper()}",
        quotation_id=quote.id,
        customer_id=customer.id,
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("500.00"),
    )
    db.add(order)
    db.flush()

    today = datetime.date.today()
    next_bill = today + datetime.timedelta(days=30)

    sub = Subscription(
        order_id=order.id,
        quotation_line_id=qline.id,
        customer_id=customer.id,
        product_id=prod.id,
        plan_id=plan.id,
        quantity=Decimal("5.00"),
        unit_price=Decimal("100.00"),
        start_date=today,
        next_billing_date=next_bill,
        status=SubscriptionStatus.ACTIVE,
    )
    db.add(sub)
    db.commit()

    return {
        "customer": customer,
        "product": prod,
        "plan": plan,
        "order": order,
        "quotation_line": qline,
        "subscription": sub,
    }


def test_subscription_plan_crud_and_rbac(
    client: TestClient, finance_user: User, sales_rep_user: User, customer_user: User
):
    """Test full CRUD on subscription plans and RBAC permissions."""
    # 1. Create plan (Finance user)
    create_payload = {
        "name": "Enterprise Annual",
        "billing_interval": "YEARLY",
        "interval_count": 1,
        "proration_method": "DAILY_PRO_RATA",
        "cancellation_policy": "END_OF_TERM",
        "refund_policy": "NO_REFUND",
        "is_active": True,
    }
    create_res = client.post(
        "/api/v1/subscription-plans",
        json=create_payload,
        headers=_auth(finance_user),
    )
    assert create_res.status_code == 201
    plan_data = create_res.json()
    plan_id = plan_data["id"]
    assert plan_data["name"] == "Enterprise Annual"
    assert plan_data["billing_interval"] == "YEARLY"

    # 2. Sales rep can list and view
    get_res = client.get(
        f"/api/v1/subscription-plans/{plan_id}", headers=_auth(sales_rep_user)
    )
    assert get_res.status_code == 200

    # 3. Update plan (Finance)
    patch_res = client.patch(
        f"/api/v1/subscription-plans/{plan_id}",
        json={"name": "Enterprise Annual Pro"},
        headers=_auth(finance_user),
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Enterprise Annual Pro"

    # 4. Soft deactivate plan
    del_res = client.delete(
        f"/api/v1/subscription-plans/{plan_id}", headers=_auth(finance_user)
    )
    assert del_res.status_code == 200
    assert del_res.json()["is_active"] is False

    # 5. Customer forbidden (403)
    cust_res = client.get("/api/v1/subscription-plans", headers=_auth(customer_user))
    assert cust_res.status_code == 403

    # Sales rep cannot create plans (403)
    rep_create = client.post(
        "/api/v1/subscription-plans", json=create_payload, headers=_auth(sales_rep_user)
    )
    assert rep_create.status_code == 403


def test_subscription_lifecycle_and_proration(
    client: TestClient, finance_user: User, subscription_setup: dict
):
    """Test subscription details, proration preview, modify, pause, and cancel."""
    sub = subscription_setup["subscription"]

    # 1. Get subscription details
    get_res = client.get(
        f"/api/v1/subscriptions/{sub.id}", headers=_auth(finance_user)
    )
    assert get_res.status_code == 200
    sub_data = get_res.json()
    assert float(sub_data["quantity"]) == 5.0
    assert float(sub_data["unit_price"]) == 100.0
    assert float(sub_data["recurring_amount"]) == 500.0

    # 2. Preview proration for upgrade to 8 seats
    preview_res = client.post(
        f"/api/v1/subscriptions/{sub.id}/proration/preview",
        json={"new_quantity": 8.0},
        headers=_auth(finance_user),
    )
    assert preview_res.status_code == 200
    prev = preview_res.json()
    assert float(prev["current_amount"]) == 500.0
    assert float(prev["new_amount"]) == 800.0
    assert float(prev["proration_adjustment"]) > 0

    # 3. Modify subscription to 8 seats
    modify_res = client.post(
        f"/api/v1/subscriptions/{sub.id}/modify",
        json={"quantity": 8.0},
        headers=_auth(finance_user),
    )
    assert modify_res.status_code == 200
    assert float(modify_res.json()["quantity"]) == 8.0
    assert modify_res.json()["status"] == "MODIFIED"

    # 4. Pause subscription
    pause_res = client.post(
        f"/api/v1/subscriptions/{sub.id}/pause", headers=_auth(finance_user)
    )
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "PAUSED"

    # 5. Cancel subscription with credit note
    cancel_res = client.post(
        f"/api/v1/subscriptions/{sub.id}/cancel",
        json={"reason": "Customer requested cancellation", "issue_credit_note": True},
        headers=_auth(finance_user),
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"
