"""Integration tests for Hybrid Billing (combining one-time and recurring lines in one order)."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import (
    BillingInterval,
    InvoiceStatus,
    InvoiceType,
    OrderStatus,
    ProrationMethod,
    QuotationStatus,
    UserRole,
)
from app.core.security import create_access_token, hash_password
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.order import Order
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuotationLine
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User


def _auth(user: User) -> dict:
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def finance_admin(db: Session) -> User:
    user = User(
        name="Finance Admin",
        email=f"fin-hybrid-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_hybrid_order_billing_e2e(
    client: TestClient, finance_admin: User, db: Session
):
    """
    Test complete Hybrid Order flow:
    Order with one-time & recurring lines ->
    Billing Generation (One-time Invoice + Subscription & Schedule) ->
    Schedule to Recurring Invoice ->
    Payments applied to both ->
    Complete status & Audit trail verified.
    """
    # 1. Setup Customer
    tier = CustomerTier(
        name=f"Diamond-{uuid.uuid4().hex[:4]}",
        default_discount_limit=Decimal("20.00"),
        is_active=True,
    )
    db.add(tier)
    db.flush()

    customer = Customer(
        name="Nexus Innovations",
        customer_tier_id=tier.id,
        is_active=True,
    )
    db.add(customer)
    db.flush()

    cat = ProductCategory(
        name=f"Hybrid Category-{uuid.uuid4().hex[:4]}",
        is_active=True,
    )
    db.add(cat)
    db.flush()

    # 2. Product 1: One-time hardware device ($1500, tax 10%)
    prod_hardware = Product(
        name="Edge Gateway Appliance",
        sku=f"HW-{uuid.uuid4().hex[:6].upper()}",
        category_id=cat.id,
        unit="DEVICE",
        base_price=Decimal("1500.00"),
        cost_price=Decimal("900.00"),
        tax_rate=Decimal("10.00"),
        is_subscription=False,
        is_active=True,
    )
    # Product 2: Recurring cloud telemetry ($100/mo, tax 0%)
    prod_saas = Product(
        name="Cloud Telemetry License",
        sku=f"SaaS-{uuid.uuid4().hex[:6].upper()}",
        category_id=cat.id,
        unit="LICENSE",
        base_price=Decimal("100.00"),
        cost_price=Decimal("15.00"),
        tax_rate=Decimal("0.00"),
        is_subscription=True,
        is_active=True,
    )
    db.add(prod_hardware)
    db.add(prod_saas)

    # Subscription plan
    plan = SubscriptionPlan(
        name="Monthly Telemetry Plan",
        billing_interval=BillingInterval.MONTHLY,
        interval_count=1,
        proration_method=ProrationMethod.DAILY_PRO_RATA,
        cancellation_policy="IMMEDIATE",
        refund_policy="PRO_RATA",
        is_active=True,
    )
    db.add(plan)
    db.flush()

    # 3. Create Quotation with BOTH one-time and recurring lines
    quote = Quotation(
        quotation_number=f"QT-HYB-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer.id,
        sales_rep_id=finance_admin.id,
        status=QuotationStatus.CONFIRMED,
        subtotal=Decimal("2000.00"),
        total_amount=Decimal("2150.00"),
    )
    db.add(quote)
    db.flush()

    # Hardware line: 1 unit @ $1500 = $1500
    line_hw = QuotationLine(
        quotation_id=quote.id,
        product_id=prod_hardware.id,
        quantity=Decimal("1.00"),
        unit_price=Decimal("1500.00"),
        line_total=Decimal("1500.00"),
    )
    # SaaS line: 5 units @ $100 = $500
    line_saas = QuotationLine(
        quotation_id=quote.id,
        product_id=prod_saas.id,
        quantity=Decimal("5.00"),
        unit_price=Decimal("100.00"),
        line_total=Decimal("500.00"),
    )
    db.add(line_hw)
    db.add(line_saas)
    db.flush()

    order = Order(
        order_number=f"SO-HYB-{uuid.uuid4().hex[:6].upper()}",
        quotation_id=quote.id,
        customer_id=customer.id,
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("2150.00"),
    )
    db.add(order)
    db.commit()

    # 4. Generate Hybrid Billing
    gen_res = client.post(
        f"/api/v1/orders/{order.id}/billing/generate",
        headers=_auth(finance_admin),
    )
    assert gen_res.status_code == 200
    billing_data = gen_res.json()

    # Validate separation: 1 one-time line, 1 recurring line
    assert len(billing_data["one_time_lines"]) == 1
    assert len(billing_data["recurring_lines"]) == 1
    assert len(billing_data["subscriptions"]) == 1
    assert len(billing_data["invoices"]) == 1

    one_time_inv = billing_data["invoices"][0]
    assert one_time_inv["invoice_type"] == "ONE_TIME"
    assert float(one_time_inv["total_amount"]) == 1650.0  # 1500 + 10% tax = 1650
    sub_id = billing_data["subscriptions"][0]["id"]

    # 5. Fetch Billing Schedule generated for Subscription
    scheds = client.get(
        f"/api/v1/billing-schedules?subscription_id={sub_id}",
        headers=_auth(finance_admin),
    ).json()
    assert len(scheds) == 1
    sched_id = scheds[0]["id"]
    assert float(scheds[0]["amount"]) == 500.0
    assert scheds[0]["status"] == "SCHEDULED"

    # 6. Generate recurring invoice from scheduled billing event
    rec_inv_res = client.post(
        f"/api/v1/billing-schedules/{sched_id}/generate-invoice",
        headers=_auth(finance_admin),
    )
    assert rec_inv_res.status_code == 200
    rec_inv = rec_inv_res.json()
    assert rec_inv["invoice_type"] == "RECURRING"
    assert float(rec_inv["total_amount"]) == 500.0
    assert rec_inv["status"] == "ISSUED"

    # 7. Pay One-Time Invoice in full ($1650)
    client.post(
        f"/api/v1/invoices/{one_time_inv['id']}/payments",
        json={"amount": 1650.0, "payment_method": "WIRE_TRANSFER"},
        headers=_auth(finance_admin),
    )

    # 8. Pay Recurring Invoice in full ($500)
    client.post(
        f"/api/v1/invoices/{rec_inv['id']}/payments",
        json={"amount": 500.0, "payment_method": "AUTO_DEBIT"},
        headers=_auth(finance_admin),
    )

    # 9. Verify Final Order Billing State
    final_billing = client.get(
        f"/api/v1/orders/{order.id}/billing", headers=_auth(finance_admin)
    ).json()
    assert len(final_billing["invoices"]) == 2
    assert all(inv["status"] == "PAID" for inv in final_billing["invoices"])
    assert float(final_billing["total_paid"]) == 2150.0
    assert float(final_billing["balance_due"]) == 0.0
    assert final_billing["billing_complete"] is True

    # 10. Verify Audit Trail
    audit_stmt = select(AuditLog).where(AuditLog.entity_id == order.id)
    order_audits = list(db.scalars(audit_stmt).all())
    actions = {a.action for a in order_audits}
    assert "BILLING_GENERATE" in actions
