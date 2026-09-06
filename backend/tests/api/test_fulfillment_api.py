"""API tests for Order Fulfillment and Backorder endpoints."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import (
    BackorderStatus,
    FulfillmentAllocationStatus,
    OrderStatus,
    QuotationStatus,
    UserRole,
)
from app.core.security import create_access_token, hash_password
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
def ops_user(db: Session) -> User:
    user = User(
        name="Ops Manager",
        email=f"ops-ful-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Ops123!"),
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
        email=f"rep-ful-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Rep123!"),
        role=UserRole.SALES_REP,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def fulfillment_setup(db: Session, sales_rep_user: User) -> dict:
    """Setup customer, product, warehouses, inventory, quotation, and confirmed order."""
    tier = CustomerTier(
        name=f"Platinum-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("25.00"),
        is_active=True,
    )
    db.add(tier)
    db.flush()

    customer = Customer(
        name="TechCorp Global",
        customer_tier_id=tier.id,
        is_active=True,
    )
    db.add(customer)
    db.flush()

    cat = ProductCategory(
        name=f"Hardware-{uuid.uuid4().hex[:4]}",
        is_active=True,
    )
    db.add(cat)
    db.flush()

    prod = Product(
        name="Enterprise Workstation",
        sku=f"WS-{uuid.uuid4().hex[:6].upper()}",
        category_id=cat.id,
        unit="UNIT",
        base_price=Decimal("2000.00"),
        cost_price=Decimal("1200.00"),
        tax_rate=Decimal("10.00"),
        is_active=True,
    )
    db.add(prod)
    db.flush()

    wh1 = Warehouse(
        name="North Hub",
        code=f"WH-N-{uuid.uuid4().hex[:4].upper()}",
        shipping_cost_weight=Decimal("1.00"),
        is_active=True,
    )
    wh2 = Warehouse(
        name="South Hub",
        code=f"WH-S-{uuid.uuid4().hex[:4].upper()}",
        shipping_cost_weight=Decimal("1.50"),
        is_active=True,
    )
    db.add(wh1)
    db.add(wh2)
    db.flush()

    # Stock: WH1 has 15, WH2 has 25
    inv1 = Inventory(
        warehouse_id=wh1.id,
        product_id=prod.id,
        quantity_on_hand=Decimal("15.00"),
        quantity_reserved=Decimal("0.00"),
    )
    inv2 = Inventory(
        warehouse_id=wh2.id,
        product_id=prod.id,
        quantity_on_hand=Decimal("25.00"),
        quantity_reserved=Decimal("0.00"),
    )
    db.add(inv1)
    db.add(inv2)
    db.flush()

    quote = Quotation(
        quotation_number=f"QT-{uuid.uuid4().hex[:8].upper()}",
        customer_id=customer.id,
        sales_rep_id=sales_rep_user.id,
        status=QuotationStatus.CONFIRMED,
        subtotal=Decimal("40000.00"),
        total_amount=Decimal("40000.00"),
    )
    db.add(quote)
    db.flush()

    qline = QuotationLine(
        quotation_id=quote.id,
        product_id=prod.id,
        quantity=Decimal("20.00"),  # Request 20 units
        unit_price=Decimal("2000.00"),
        line_total=Decimal("40000.00"),
    )
    db.add(qline)
    db.flush()

    order = Order(
        order_number=f"SO-{uuid.uuid4().hex[:8].upper()}",
        quotation_id=quote.id,
        customer_id=customer.id,
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("40000.00"),
    )
    db.add(order)
    db.commit()

    return {
        "customer": customer,
        "product": prod,
        "warehouse1": wh1,
        "warehouse2": wh2,
        "inventory1": inv1,
        "inventory2": inv2,
        "quotation": quote,
        "quotation_line": qline,
        "order": order,
    }


def test_order_fulfillment_suggest_and_accept(
    client: TestClient, ops_user: User, fulfillment_setup: dict, db: Session
):
    """Test suggesting warehouse allocation split, accepting it, and verifying reservations."""
    order = fulfillment_setup["order"]
    wh1 = fulfillment_setup["warehouse1"]
    wh2 = fulfillment_setup["warehouse2"]

    # 1. Suggest split: WH1 has 15, WH2 has 25.
    # Single warehouse WH2 can satisfy all 20 units!
    suggest_res = client.post(
        f"/api/v1/orders/{order.id}/fulfillment/suggest",
        headers=_auth(ops_user),
    )
    assert suggest_res.status_code == 200
    summary = suggest_res.json()
    assert summary["order_id"] == str(order.id)
    assert len(summary["allocations"]) == 1
    assert summary["allocations"][0]["warehouse_id"] == str(wh2.id)
    assert float(summary["allocations"][0]["quantity_allocated"]) == 20.0
    assert summary["allocations"][0]["status"] == "SUGGESTED"

    # 2. Accept split
    accept_res = client.post(
        f"/api/v1/orders/{order.id}/fulfillment/accept",
        headers=_auth(ops_user),
    )
    assert accept_res.status_code == 200
    accepted_summary = accept_res.json()
    assert accepted_summary["order_status"] == "FULFILLMENT"
    assert accepted_summary["allocations"][0]["status"] == "ACCEPTED"

    # Verify inventory reserved in db
    db.expire_all()
    inv2 = db.get(Inventory, fulfillment_setup["inventory2"].id)
    assert inv2.quantity_reserved == Decimal("20.00")
    assert inv2.available_stock == Decimal("5.00")


def test_fulfillment_complete_deducts_stock(
    client: TestClient, ops_user: User, fulfillment_setup: dict, db: Session
):
    """Test that completing fulfillment marks allocations fulfilled and deducts inventory on-hand."""
    order = fulfillment_setup["order"]

    # Suggest + Accept
    client.post(f"/api/v1/orders/{order.id}/fulfillment/suggest", headers=_auth(ops_user))
    client.post(f"/api/v1/orders/{order.id}/fulfillment/accept", headers=_auth(ops_user))

    # Complete fulfillment
    complete_res = client.post(
        f"/api/v1/orders/{order.id}/fulfillment/complete",
        headers=_auth(ops_user),
    )
    assert complete_res.status_code == 200
    comp_summary = complete_res.json()
    assert comp_summary["order_status"] == "FULFILLED"
    assert comp_summary["allocations"][0]["status"] == "FULFILLED"
    assert float(comp_summary["total_quantity_fulfilled"]) == 20.0

    # Verify physical stock deducted
    db.expire_all()
    inv2 = db.get(Inventory, fulfillment_setup["inventory2"].id)
    assert inv2.quantity_on_hand == Decimal("5.00")  # 25 - 20
    assert inv2.quantity_reserved == Decimal("0.00")  # 20 - 20


def test_manual_override_fulfillment(
    client: TestClient, ops_user: User, fulfillment_setup: dict, db: Session
):
    """Test manually overriding warehouse allocations."""
    order = fulfillment_setup["order"]
    qline = fulfillment_setup["quotation_line"]
    wh1 = fulfillment_setup["warehouse1"]
    wh2 = fulfillment_setup["warehouse2"]

    # Manual split: 10 from WH1 and 10 from WH2
    override_payload = {
        "allocations": [
            {"quotation_line_id": str(qline.id), "warehouse_id": str(wh1.id), "quantity_allocated": 10.0},
            {"quotation_line_id": str(qline.id), "warehouse_id": str(wh2.id), "quantity_allocated": 10.0},
        ]
    }

    override_res = client.post(
        f"/api/v1/orders/{order.id}/fulfillment/override",
        json=override_payload,
        headers=_auth(ops_user),
    )
    assert override_res.status_code == 200
    summary = override_res.json()
    assert summary["order_status"] == "FULFILLMENT"
    assert len(summary["allocations"]) == 2
    assert summary["is_split"] is True

    # Check reservations
    db.expire_all()
    inv1 = db.get(Inventory, fulfillment_setup["inventory1"].id)
    inv2 = db.get(Inventory, fulfillment_setup["inventory2"].id)
    assert inv1.quantity_reserved == Decimal("10.00")
    assert inv2.quantity_reserved == Decimal("10.00")


def test_backorder_consolidation_and_cancellation(
    client: TestClient, ops_user: User, fulfillment_setup: dict, db: Session
):
    """Test backorder creation when stock is insufficient, and consolidation once replenished."""
    order = fulfillment_setup["order"]
    qline = fulfillment_setup["quotation_line"]
    wh1 = fulfillment_setup["warehouse1"]

    # Override: allocate only 12 units -> 8 must be backordered
    override_payload = {
        "allocations": [
            {"quotation_line_id": str(qline.id), "warehouse_id": str(wh1.id), "quantity_allocated": 12.0}
        ]
    }
    client.post(
        f"/api/v1/orders/{order.id}/fulfillment/override",
        json=override_payload,
        headers=_auth(ops_user),
    )

    # Check backorders
    bo_res = client.get(f"/api/v1/orders/{order.id}/backorders", headers=_auth(ops_user))
    assert bo_res.status_code == 200
    backorders = bo_res.json()
    assert len(backorders) == 1
    bo_id = backorders[0]["id"]
    assert float(backorders[0]["quantity_backordered"]) == 8.0
    assert float(backorders[0]["quantity_remaining"]) == 8.0
    assert backorders[0]["status"] == "OPEN"

    # Consolidate backorder: WH2 still has 25 units available!
    cons_res = client.post(
        f"/api/v1/backorders/{bo_id}/consolidate", headers=_auth(ops_user)
    )
    assert cons_res.status_code == 200
    cons_data = cons_res.json()
    assert cons_data["status"] == "CONSOLIDATED"
    assert float(cons_data["quantity_remaining"]) == 0.0

    # Verify backorders list
    all_bos = client.get("/api/v1/backorders", headers=_auth(ops_user))
    assert all_bos.status_code == 200
    assert any(b["id"] == bo_id for b in all_bos.json())


def test_allocation_patch_and_backorder_cancel(
    client: TestClient, ops_user: User, fulfillment_setup: dict, db: Session
):
    """Test updating a single allocation and cancelling a backorder."""
    order = fulfillment_setup["order"]
    qline = fulfillment_setup["quotation_line"]
    wh1 = fulfillment_setup["warehouse1"]

    # 1. Manual override to create an allocation and an open backorder
    override_payload = {
        "allocations": [
            {"quotation_line_id": str(qline.id), "warehouse_id": str(wh1.id), "quantity_allocated": 10.0}
        ]
    }
    client.post(
        f"/api/v1/orders/{order.id}/fulfillment/override",
        json=override_payload,
        headers=_auth(ops_user),
    )

    allocations = client.get(
        f"/api/v1/orders/{order.id}/fulfillment/allocations",
        headers=_auth(ops_user),
    ).json()
    assert len(allocations) == 1
    alloc_id = allocations[0]["id"]

    # 2. Patch allocation quantity from 10 to 12
    patch_res = client.patch(
        f"/api/v1/orders/{order.id}/fulfillment/allocations/{alloc_id}",
        json={"quantity_allocated": 12.0},
        headers=_auth(ops_user),
    )
    assert patch_res.status_code == 200
    assert float(patch_res.json()["quantity_allocated"]) == 12.0

    # 3. Cancel the remaining open backorder
    bos = client.get(f"/api/v1/orders/{order.id}/backorders", headers=_auth(ops_user)).json()
    assert len(bos) == 1
    cancel_res = client.post(
        f"/api/v1/backorders/{bos[0]['id']}/cancel",
        headers=_auth(ops_user),
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"


def test_fulfillment_rbac_and_edge_cases(
    client: TestClient,
    sales_rep_user: User,
    ops_user: User,
    fulfillment_setup: dict,
    db: Session,
):
    """Verify RBAC restrictions and error conditions."""
    order = fulfillment_setup["order"]

    # Customer user
    customer_user = User(
        name="External Customer",
        email=f"cust-rbac-{uuid.uuid4().hex[:6]}@client.com",
        password_hash=hash_password("Pass123!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(customer_user)
    db.commit()

    # 1. Customer cannot view fulfillment
    res_cust = client.get(
        f"/api/v1/orders/{order.id}/fulfillment",
        headers=_auth(customer_user),
    )
    assert res_cust.status_code == 403

    # 2. Sales rep cannot perform manual override or completion
    res_rep_ovr = client.post(
        f"/api/v1/orders/{order.id}/fulfillment/override",
        json={"allocations": []},
        headers=_auth(sales_rep_user),
    )
    assert res_rep_ovr.status_code == 403

    res_rep_comp = client.post(
        f"/api/v1/orders/{order.id}/fulfillment/complete",
        headers=_auth(sales_rep_user),
    )
    assert res_rep_comp.status_code == 403

    # 3. Non-existent order returns 404
    fake_id = uuid.uuid4()
    res_404 = client.get(
        f"/api/v1/orders/{fake_id}/fulfillment",
        headers=_auth(ops_user),
    )
    assert res_404.status_code == 404
