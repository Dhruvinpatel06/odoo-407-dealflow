"""API tests for Inventory endpoints."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import create_access_token, hash_password
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.user import User
from app.models.warehouse import Warehouse


def _auth(user: User) -> dict:
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ops_user(db: Session) -> User:
    user = User(
        name="Inventory Manager",
        email=f"inv-ops-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
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
def inventory_setup(db: Session) -> dict:
    cat = ProductCategory(
        name=f"Hardware-{uuid.uuid4().hex[:4]}",
        is_active=True,
    )
    db.add(cat)
    db.flush()

    prod = Product(
        name="Enterprise Server Pro",
        sku=f"SRV-{uuid.uuid4().hex[:6].upper()}",
        category_id=cat.id,
        unit="UNIT",
        base_price=Decimal("1200.00"),
        cost_price=Decimal("750.00"),
        tax_rate=Decimal("10.00"),
        is_active=True,
    )
    db.add(prod)
    db.flush()

    wh1 = Warehouse(
        name="Chicago Hub",
        code=f"WH-CHI-{uuid.uuid4().hex[:4].upper()}",
        shipping_cost_weight=Decimal("1.00"),
        is_active=True,
    )
    wh2 = Warehouse(
        name="Atlanta Hub",
        code=f"WH-ATL-{uuid.uuid4().hex[:4].upper()}",
        shipping_cost_weight=Decimal("1.20"),
        is_active=True,
    )
    db.add(wh1)
    db.add(wh2)
    db.commit()

    return {"product": prod, "warehouse1": wh1, "warehouse2": wh2}


def test_inventory_creation_and_product_aggregation(
    client: TestClient, ops_user: User, rep_user: User, inventory_setup: dict
):
    """Test stock configuration across multiple warehouses and product aggregation."""
    prod = inventory_setup["product"]
    wh1 = inventory_setup["warehouse1"]
    wh2 = inventory_setup["warehouse2"]

    # 1. Set stock in wh1: 50 units
    res1 = client.post(
        f"/api/v1/warehouses/{wh1.id}/inventory",
        json={"product_id": str(prod.id), "quantity_on_hand": 50.0, "reorder_level": 10.0},
        headers=_auth(ops_user),
    )
    assert res1.status_code == 201
    data1 = res1.json()
    assert float(data1["quantity_on_hand"]) == 50.0
    assert float(data1["available_stock"]) == 50.0

    # 2. Set stock in wh2: 30 units
    res2 = client.post(
        f"/api/v1/warehouses/{wh2.id}/inventory",
        json={"product_id": str(prod.id), "quantity_on_hand": 30.0, "reorder_level": 5.0},
        headers=_auth(ops_user),
    )
    assert res2.status_code == 201

    # 3. Query product inventory across warehouses
    agg_res = client.get(
        f"/api/v1/inventory/product/{prod.id}", headers=_auth(rep_user)
    )
    assert agg_res.status_code == 200
    agg = agg_res.json()
    assert agg["product_name"] == "Enterprise Server Pro"
    assert float(agg["total_on_hand"]) == 80.0
    assert float(agg["total_available"]) == 80.0
    assert len(agg["warehouses"]) == 2

    # 4. List inventory for wh1
    wh1_inv = client.get(
        f"/api/v1/warehouses/{wh1.id}/inventory", headers=_auth(rep_user)
    )
    assert wh1_inv.status_code == 200
    assert len(wh1_inv.json()) == 1


def test_inventory_patch_and_validation(
    client: TestClient, ops_user: User, inventory_setup: dict
):
    """Test updating stock and validating reservation constraints."""
    prod = inventory_setup["product"]
    wh1 = inventory_setup["warehouse1"]

    create_res = client.post(
        f"/api/v1/warehouses/{wh1.id}/inventory",
        json={"product_id": str(prod.id), "quantity_on_hand": 100.0},
        headers=_auth(ops_user),
    )
    inv_id = create_res.json()["id"]

    # Valid update: reserve 20
    patch_res = client.patch(
        f"/api/v1/inventory/{inv_id}",
        json={"quantity_reserved": 20.0},
        headers=_auth(ops_user),
    )
    assert patch_res.status_code == 200
    assert float(patch_res.json()["available_stock"]) == 80.0

    # Invalid update: reserved > on_hand
    bad_patch = client.patch(
        f"/api/v1/inventory/{inv_id}",
        json={"quantity_reserved": 150.0},
        headers=_auth(ops_user),
    )
    assert bad_patch.status_code == 422  # BusinessRuleViolationError
