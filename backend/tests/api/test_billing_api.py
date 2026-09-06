"""API tests for Billing, Invoices, Billing Schedules, and Payments endpoints."""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import (
    BillingInterval,
    InvoiceStatus,
    InvoiceType,
    OrderStatus,
    PaymentStatus,
    ProrationMethod,
    QuotationStatus,
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
from app.models.user import User


def _auth(user: User) -> dict:
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def finance_user(db: Session) -> User:
    user = User(
        name="Finance Officer",
        email=f"fin-bil-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Pass123!"),
        role=UserRole.FINANCE_OPERATIONS,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def rep_user(db: Session) -> User:
    user = User(
        name="Sales User",
        email=f"rep-bil-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Pass123!"),
        role=UserRole.SALES_REP,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def billing_setup(db: Session, rep_user: User) -> dict:
    tier = CustomerTier(
        name=f"Gold-Bil-{uuid.uuid4().hex[:4]}",
        default_discount_limit=Decimal("15.00"),
        is_active=True,
    )
    db.add(tier)
    db.flush()

    customer = Customer(
        name="Apex Industrial",
        customer_tier_id=tier.id,
        is_active=True,
    )
    db.add(customer)
    db.flush()

    cat = ProductCategory(
        name=f"Industrial Goods-{uuid.uuid4().hex[:4]}",
        is_active=True,
    )
    db.add(cat)
    db.flush()

    # One-time product
    prod = Product(
        name="Industrial Pump",
        sku=f"PUMP-{uuid.uuid4().hex[:6].upper()}",
        category_id=cat.id,
        unit="PIECE",
        base_price=Decimal("1000.00"),
        cost_price=Decimal("600.00"),
        tax_rate=Decimal("10.00"),
        is_subscription=False,
        is_active=True,
    )
    db.add(prod)
    db.flush()

    quote = Quotation(
        quotation_number=f"QT-BIL-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer.id,
        sales_rep_id=rep_user.id,
        status=QuotationStatus.CONFIRMED,
        subtotal=Decimal("2000.00"),
        total_amount=Decimal("2200.00"),
    )
    db.add(quote)
    db.flush()

    qline = QuotationLine(
        quotation_id=quote.id,
        product_id=prod.id,
        quantity=Decimal("2.00"),
        unit_price=Decimal("1000.00"),
        line_total=Decimal("2000.00"),
    )
    db.add(qline)
    db.flush()

    order = Order(
        order_number=f"SO-BIL-{uuid.uuid4().hex[:6].upper()}",
        quotation_id=quote.id,
        customer_id=customer.id,
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("2200.00"),
    )
    db.add(order)
    db.commit()

    return {
        "customer": customer,
        "product": prod,
        "order": order,
        "quotation_line": qline,
    }


def test_order_billing_generation_and_payment_flow(
    client: TestClient, finance_user: User, rep_user: User, billing_setup: dict
):
    """Test generating billing, recording partial and full payments, and checking invoice status."""
    order = billing_setup["order"]

    # 1. Generate billing for confirmed order
    gen_res = client.post(
        f"/api/v1/orders/{order.id}/billing/generate",
        headers=_auth(finance_user),
    )
    assert gen_res.status_code == 200
    billing_data = gen_res.json()
    assert billing_data["order_id"] == str(order.id)
    assert len(billing_data["invoices"]) == 1
    invoice = billing_data["invoices"][0]
    inv_id = invoice["id"]
    assert float(invoice["total_amount"]) == 2200.0  # 2000 subtotal + 10% tax (200)
    assert float(invoice["paid_amount"]) == 0.0
    assert invoice["status"] == "ISSUED"

    # 2. Record partial payment of $1200
    pay1_res = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"amount": 1200.0, "payment_method": "BANK_TRANSFER"},
        headers=_auth(finance_user),
    )
    assert pay1_res.status_code == 201
    pay1 = pay1_res.json()
    assert float(pay1["amount"]) == 1200.0
    assert pay1["status"] == "RECORDED"

    # Check invoice status updated to PARTIALLY_PAID
    inv_check1 = client.get(f"/api/v1/invoices/{inv_id}", headers=_auth(rep_user)).json()
    assert inv_check1["status"] == "PARTIALLY_PAID"
    assert float(inv_check1["paid_amount"]) == 1200.0
    assert float(inv_check1["balance_due"]) == 1000.0

    # 3. Attempt overpayment (Remaining due: $1000, paying $1500) -> Must fail with 422!
    overpay_res = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"amount": 1500.0, "payment_method": "CREDIT_CARD"},
        headers=_auth(finance_user),
    )
    assert overpay_res.status_code == 422

    # 4. Final payment of remaining $1000 -> Status becomes PAID
    pay2_res = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"amount": 1000.0, "payment_method": "CREDIT_CARD"},
        headers=_auth(finance_user),
    )
    assert pay2_res.status_code == 201

    inv_check2 = client.get(f"/api/v1/invoices/{inv_id}", headers=_auth(rep_user)).json()
    assert inv_check2["status"] == "PAID"
    assert float(inv_check2["paid_amount"]) == 2200.0
    assert float(inv_check2["balance_due"]) == 0.0


def test_payment_refund_and_invoice_reversion(
    client: TestClient, finance_user: User, billing_setup: dict
):
    """Test refunding a payment reverts the invoice paid amount and status."""
    order = billing_setup["order"]

    # Generate billing
    client.post(f"/api/v1/orders/{order.id}/billing/generate", headers=_auth(finance_user))
    invoices = client.get(f"/api/v1/invoices?order_id={order.id}", headers=_auth(finance_user)).json()
    inv_id = invoices[0]["id"]

    # Pay in full
    pay_res = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"amount": 2200.0, "payment_method": "ACH"},
        headers=_auth(finance_user),
    )
    pay_id = pay_res.json()["id"]

    # Refund the payment
    refund_res = client.post(
        f"/api/v1/payments/{pay_id}/refund",
        headers=_auth(finance_user),
    )
    assert refund_res.status_code == 200
    assert refund_res.json()["status"] == "REFUNDED"

    # Invoice reverts to ISSUED
    inv = client.get(f"/api/v1/invoices/{inv_id}", headers=_auth(finance_user)).json()
    assert inv["status"] == "ISSUED"
    assert float(inv["paid_amount"]) == 0.0


def test_credit_note_creation(
    client: TestClient, finance_user: User, billing_setup: dict
):
    """Test creating an explicit credit note against an order."""
    order = billing_setup["order"]

    cn_res = client.post(
        f"/api/v1/orders/{order.id}/credit-notes",
        json={"amount": 250.0, "reason": "Customer loyalty rebate"},
        headers=_auth(finance_user),
    )
    assert cn_res.status_code == 201
    cn = cn_res.json()
    assert cn["invoice_type"] == "CREDIT_NOTE"
    assert float(cn["total_amount"]) == 250.0
    assert cn["status"] == "ISSUED"
