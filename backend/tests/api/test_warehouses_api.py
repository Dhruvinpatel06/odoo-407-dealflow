"""API tests for Warehouses endpoints."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import create_access_token, hash_password
from app.models.user import User


def _auth(user: User) -> dict:
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ops_user(db: Session) -> User:
    user = User(
        name="Ops Specialist",
        email=f"ops-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("OpsPass123!"),
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
        name="Sales Rep",
        email=f"rep-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("RepPass123!"),
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
        password_hash=hash_password("CustPass123!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_warehouse_crud_flow(
    client: TestClient, admin_user: User, rep_user: User
):
    """Test full CRUD lifecycle for a warehouse."""
    code = f"WH-{uuid.uuid4().hex[:4].upper()}"
    create_payload = {
        "name": "Dallas Logistics Hub",
        "code": code,
        "address": "123 Logistics Blvd, Dallas TX",
        "shipping_cost_weight": 1.25,
        "replenishment_enabled": True,
        "is_active": True,
    }

    # 1. Create warehouse (admin)
    create_res = client.post(
        "/api/v1/warehouses", json=create_payload, headers=_auth(admin_user)
    )
    assert create_res.status_code == 201
    wh = create_res.json()
    wh_id = wh["id"]
    assert wh["code"] == code
    assert float(wh["shipping_cost_weight"]) == 1.25
    assert wh["is_active"] is True

    # 2. Get warehouse (sales rep can read)
    get_res = client.get(f"/api/v1/warehouses/{wh_id}", headers=_auth(rep_user))
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Dallas Logistics Hub"

    # 3. List warehouses
    list_res = client.get("/api/v1/warehouses", headers=_auth(rep_user))
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(item["id"] == wh_id for item in items)

    # 4. Patch warehouse
    patch_res = client.patch(
        f"/api/v1/warehouses/{wh_id}",
        json={"name": "Dallas Super Hub", "shipping_cost_weight": 1.10},
        headers=_auth(admin_user),
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Dallas Super Hub"
    assert float(patch_res.json()["shipping_cost_weight"]) == 1.10

    # 5. Soft-delete / deactivate
    del_res = client.delete(
        f"/api/v1/warehouses/{wh_id}", headers=_auth(admin_user)
    )
    assert del_res.status_code == 200
    assert del_res.json()["is_active"] is False


def test_warehouse_code_uniqueness(client: TestClient, ops_user: User):
    """Verify unique constraint on warehouse code."""
    code = f"WH-UNIQ-{uuid.uuid4().hex[:4].upper()}"
    payload = {
        "name": "Warehouse Alpha",
        "code": code,
        "shipping_cost_weight": 1.0,
    }

    res1 = client.post("/api/v1/warehouses", json=payload, headers=_auth(ops_user))
    assert res1.status_code == 201

    res2 = client.post("/api/v1/warehouses", json=payload, headers=_auth(ops_user))
    assert res2.status_code == 422  # BusinessRuleViolationError


def test_warehouse_rbac_matrix(
    client: TestClient,
    admin_user: User,
    ops_user: User,
    rep_user: User,
    customer_user: User,
):
    """Verify role permissions across warehouse endpoints."""
    code = f"WH-RBAC-{uuid.uuid4().hex[:4].upper()}"
    payload = {"name": "RBAC WH", "code": code, "shipping_cost_weight": 1.0}

    # Customer cannot read or write
    res_cust_get = client.get("/api/v1/warehouses", headers=_auth(customer_user))
    assert res_cust_get.status_code == 403

    res_cust_post = client.post("/api/v1/warehouses", json=payload, headers=_auth(customer_user))
    assert res_cust_post.status_code == 403

    # Sales rep cannot write
    res_rep_post = client.post("/api/v1/warehouses", json=payload, headers=_auth(rep_user))
    assert res_rep_post.status_code == 403

    # Ops user can write
    res_ops_post = client.post("/api/v1/warehouses", json=payload, headers=_auth(ops_user))
    assert res_ops_post.status_code == 201
