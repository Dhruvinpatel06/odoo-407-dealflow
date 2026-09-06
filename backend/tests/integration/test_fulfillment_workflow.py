"""End-to-End integration tests for the DealFlow360 Fulfillment workflow."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import OrderStatus, QuotationStatus, UserRole
from app.core.security import create_access_token, hash_password
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuotationLine
from app.models.user import User
from app.models.warehouse import Warehouse


def _auth(user: User) -> dict:
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ops_admin_user(db: Session) -> User:
    user = User(
        name="Chief of Ops",
        email=f"ops-e2e-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_e2e_quotation_to_multi_warehouse_fulfillment(
    client: TestClient, ops_admin_user: User, db: Session
):
    """
    Test complete lifecycle:
    Quotation -> Order -> Multi-Warehouse Split -> Accept -> Complete -> Audit Trail.
    """
    # 1. Setup Customer and Catalog
    tier = CustomerTier(
        name=f"Enterprise Tier-{uuid.uuid4().hex[:4]}",
        default_discount_limit=Decimal("30.00"),
        is_active=True,
    )
    db.add(tier)
    db.flush()

    customer = Customer(
        name="Global Systems Inc",
        customer_tier_id=tier.id,
        is_active=True,
    )
    db.add(customer)
    db.flush()

    cat = ProductCategory(
        name=f"Networking-{uuid.uuid4().hex[:4]}",
        is_active=True,
    )
    db.add(cat)
    db.flush()

    prod = Product(
        name="Gigabit Switch 48-Port",
        sku=f"NET-{uuid.uuid4().hex[:6].upper()}",
        category_id=cat.id,
        unit="UNIT",
        base_price=Decimal("500.00"),
        cost_price=Decimal("300.00"),
        tax_rate=Decimal("10.00"),
        is_active=True,
    )
    db.add(prod)
    db.flush()

    # 2. Setup Warehouses via API
    wh1_res = client.post(
        "/api/v1/warehouses",
        json={
            "name": "East Warehouse",
            "code": f"WH-E-{uuid.uuid4().hex[:4].upper()}",
            "shipping_cost_weight": 1.00,
        },
        headers=_auth(ops_admin_user),
    )
    assert wh1_res.status_code == 201
    wh1_id = wh1_res.json()["id"]

    wh2_res = client.post(
        "/api/v1/warehouses",
        json={
            "name": "West Warehouse",
            "code": f"WH-W-{uuid.uuid4().hex[:4].upper()}",
            "shipping_cost_weight": 1.20,
        },
        headers=_auth(ops_admin_user),
    )
    assert wh2_res.status_code == 201
    wh2_id = wh2_res.json()["id"]

    # 3. Setup Inventory: East has 15, West has 20
    inv1_res = client.post(
        f"/api/v1/warehouses/{wh1_id}/inventory",
        json={"product_id": str(prod.id), "quantity_on_hand": 15.0},
        headers=_auth(ops_admin_user),
    )
    assert inv1_res.status_code == 201

    inv2_res = client.post(
        f"/api/v1/warehouses/{wh2_id}/inventory",
        json={"product_id": str(prod.id), "quantity_on_hand": 20.0},
        headers=_auth(ops_admin_user),
    )
    assert inv2_res.status_code == 201

    # 4. Create Quotation requesting 25 units (Requires Multi-Warehouse Split!)
    quote = Quotation(
        quotation_number=f"QT-E2E-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer.id,
        sales_rep_id=ops_admin_user.id,
        status=QuotationStatus.CONFIRMED,
        subtotal=Decimal("12500.00"),
        total_amount=Decimal("12500.00"),
    )
    db.add(quote)
    db.flush()

    qline = QuotationLine(
        quotation_id=quote.id,
        product_id=prod.id,
        quantity=Decimal("25.00"),
        unit_price=Decimal("500.00"),
        line_total=Decimal("12500.00"),
    )
    db.add(qline)
    db.flush()

    order = Order(
        order_number=f"SO-E2E-{uuid.uuid4().hex[:6].upper()}",
        quotation_id=quote.id,
        customer_id=customer.id,
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("12500.00"),
    )
    db.add(order)
    db.commit()

    # 5. Suggest Fulfillment Split
    suggest_res = client.post(
        f"/api/v1/orders/{order.id}/fulfillment/suggest",
        headers=_auth(ops_admin_user),
    )
    assert suggest_res.status_code == 200
    suggest_data = suggest_res.json()
    assert suggest_data["is_split"] is True
    assert suggest_data["estimated_shipment_count"] == 2
    assert len(suggest_data["allocations"]) == 2
    # WH1 has 15 (allocated 15), WH2 provides remaining 10
    wh1_alloc = next(a for a in suggest_data["allocations"] if a["warehouse_id"] == wh1_id)
    wh2_alloc = next(a for a in suggest_data["allocations"] if a["warehouse_id"] == wh2_id)
    assert float(wh1_alloc["quantity_allocated"]) == 15.0
    assert float(wh2_alloc["quantity_allocated"]) == 10.0

    # 6. Accept Fulfillment
    accept_res = client.post(
        f"/api/v1/orders/{order.id}/fulfillment/accept",
        headers=_auth(ops_admin_user),
    )
    assert accept_res.status_code == 200
    accept_data = accept_res.json()
    assert accept_data["order_status"] == "FULFILLMENT"
    assert all(a["status"] == "ACCEPTED" for a in accept_data["allocations"])

    # 7. Complete Fulfillment
    complete_res = client.post(
        f"/api/v1/orders/{order.id}/fulfillment/complete",
        headers=_auth(ops_admin_user),
    )
    assert complete_res.status_code == 200
    complete_data = complete_res.json()
    assert complete_data["order_status"] == "FULFILLED"
    assert all(a["status"] == "FULFILLED" for a in complete_data["allocations"])
    assert float(complete_data["total_quantity_fulfilled"]) == 25.0

    # 8. Check Physical Stock in Warehouses
    wh1_stock = client.get(f"/api/v1/warehouses/{wh1_id}/inventory", headers=_auth(ops_admin_user)).json()[0]
    wh2_stock = client.get(f"/api/v1/warehouses/{wh2_id}/inventory", headers=_auth(ops_admin_user)).json()[0]
    assert float(wh1_stock["quantity_on_hand"]) == 0.0  # 15 - 15
    assert float(wh1_stock["quantity_reserved"]) == 0.0
    assert float(wh2_stock["quantity_on_hand"]) == 10.0  # 20 - 10
    assert float(wh2_stock["quantity_reserved"]) == 0.0

    # 9. Verify Audit Trail
    audit_stmt = select(AuditLog).where(AuditLog.entity_id == order.id)
    order_audits = list(db.scalars(audit_stmt).all())
    actions = {a.action for a in order_audits}
    assert "FULFILLMENT_ACCEPT" in actions
    assert "FULFILLMENT_COMPLETE" in actions
