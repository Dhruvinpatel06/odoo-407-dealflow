"""Tests for Product Category CRUD endpoints and authorization."""

from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import create_access_token
from app.models.discount_rule import DiscountRule
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.user import User


def _create_auth_headers(user: User) -> dict:
    """Helper to generate Authorization header for a given user."""
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


def test_create_product_category_success(client: TestClient, admin_user: User):
    """Verify ADMIN can create a valid product category."""
    headers = _create_auth_headers(admin_user)
    payload = {
        "name": "Hardware",
        "description": "Physical IT equipment and devices",
        "is_active": True,
    }
    response = client.post("/api/v1/product-categories", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Hardware"
    assert data["description"] == "Physical IT equipment and devices"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_product_category_duplicate_name_fails(client: TestClient, admin_user: User):
    """Verify creating a category with an existing name returns 400."""
    headers = _create_auth_headers(admin_user)
    payload = {
        "name": "Subscriptions",
        "description": "Recurring software plans",
    }
    resp1 = client.post("/api/v1/product-categories", json=payload, headers=headers)
    assert resp1.status_code == 201

    # Exact duplicate
    resp2 = client.post("/api/v1/product-categories", json=payload, headers=headers)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"].lower()

    # Case-insensitive duplicate
    payload_case = {"name": "subscriptions"}
    resp3 = client.post("/api/v1/product-categories", json=payload_case, headers=headers)
    assert resp3.status_code == 400
    assert "already exists" in resp3.json()["detail"].lower()


def test_create_product_category_validation_errors(client: TestClient, admin_user: User):
    """Verify empty name or missing required fields return 422 or 400."""
    headers = _create_auth_headers(admin_user)

    # Missing name
    resp_missing = client.post("/api/v1/product-categories", json={}, headers=headers)
    assert resp_missing.status_code == 422

    # Empty string name
    resp_empty = client.post("/api/v1/product-categories", json={"name": ""}, headers=headers)
    assert resp_empty.status_code == 422

    # Whitespace only name
    resp_spaces = client.post("/api/v1/product-categories", json={"name": "   "}, headers=headers)
    assert resp_spaces.status_code == 400


def test_list_product_categories(client: TestClient, admin_user: User, test_user: User):
    """Verify listing categories with optional active status filter and pagination."""
    admin_headers = _create_auth_headers(admin_user)
    rep_headers = _create_auth_headers(test_user)

    client.post(
        "/api/v1/product-categories",
        json={"name": "Cat Active A", "is_active": True},
        headers=admin_headers,
    )
    client.post(
        "/api/v1/product-categories",
        json={"name": "Cat Inactive B", "is_active": False},
        headers=admin_headers,
    )

    # Internal user (SALES_REP) can list
    resp = client.get("/api/v1/product-categories", headers=rep_headers)
    assert resp.status_code == 200
    data = resp.json()
    names = [c["name"] for c in data]
    assert "Cat Active A" in names
    assert "Cat Inactive B" in names

    # Filter active only
    resp_active = client.get("/api/v1/product-categories?is_active=true", headers=rep_headers)
    assert resp_active.status_code == 200
    active_names = [c["name"] for c in resp_active.json()]
    assert "Cat Active A" in active_names
    assert "Cat Inactive B" not in active_names

    # Filter inactive only
    resp_inactive = client.get("/api/v1/product-categories?is_active=false", headers=rep_headers)
    assert resp_inactive.status_code == 200
    inactive_names = [c["name"] for c in resp_inactive.json()]
    assert "Cat Inactive B" in inactive_names
    assert "Cat Active A" not in inactive_names


def test_get_product_category_by_id(client: TestClient, admin_user: User, test_user: User):
    """Verify retrieving category by UUID."""
    admin_headers = _create_auth_headers(admin_user)
    rep_headers = _create_auth_headers(test_user)

    create_resp = client.post(
        "/api/v1/product-categories",
        json={"name": "Consulting Services", "description": "Professional services"},
        headers=admin_headers,
    )
    cat_id = create_resp.json()["id"]

    # Retrieve by ID
    get_resp = client.get(f"/api/v1/product-categories/{cat_id}", headers=rep_headers)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == cat_id
    assert data["name"] == "Consulting Services"
    assert data["description"] == "Professional services"

    # Non-existent ID returns 404
    non_existent = str(uuid.uuid4())
    resp_404 = client.get(f"/api/v1/product-categories/{non_existent}", headers=rep_headers)
    assert resp_404.status_code == 404
    assert "not found" in resp_404.json()["detail"].lower()


def test_update_product_category(client: TestClient, admin_user: User):
    """Verify updating a category."""
    headers = _create_auth_headers(admin_user)

    create_resp = client.post(
        "/api/v1/product-categories",
        json={"name": "Initial Cat", "description": "Initial desc"},
        headers=headers,
    )
    cat_id = create_resp.json()["id"]

    # Partial update
    patch_resp = client.patch(
        f"/api/v1/product-categories/{cat_id}",
        json={"name": "Updated Cat", "description": "Updated desc"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["name"] == "Updated Cat"
    assert updated["description"] == "Updated desc"

    # Rename conflict check
    client.post(
        "/api/v1/product-categories",
        json={"name": "Existing Other Cat"},
        headers=headers,
    )
    conflict_resp = client.patch(
        f"/api/v1/product-categories/{cat_id}",
        json={"name": "Existing Other Cat"},
        headers=headers,
    )
    assert conflict_resp.status_code == 400
    assert "already exists" in conflict_resp.json()["detail"].lower()

    # Update non-existent returns 404
    resp_404 = client.patch(
        f"/api/v1/product-categories/{uuid.uuid4()}",
        json={"name": "Ghost Cat"},
        headers=headers,
    )
    assert resp_404.status_code == 404


def test_delete_product_category_logical_deactivation(
    client: TestClient, admin_user: User, db: Session
):
    """Verify DELETE performs logical deactivation."""
    headers = _create_auth_headers(admin_user)

    create_resp = client.post(
        "/api/v1/product-categories",
        json={"name": "Category To Deactivate", "is_active": True},
        headers=headers,
    )
    cat_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/product-categories/{cat_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["is_active"] is False

    # Check in DB that record is still present but deactivated
    cat_in_db = db.get(ProductCategory, uuid.UUID(cat_id))
    assert cat_in_db is not None
    assert cat_in_db.is_active is False

    # Delete non-existent category returns 404
    resp_404 = client.delete(f"/api/v1/product-categories/{uuid.uuid4()}", headers=headers)
    assert resp_404.status_code == 404


def test_product_category_role_authorization_matrix(
    client: TestClient, admin_user: User, db: Session
):
    """
    Verify role-based authorization matrix:
    - CUSTOMER: 403 on all operations (GET, POST, PATCH, DELETE).
    - SALES_REP, SALES_MANAGER, FINANCE_OPERATIONS: 200 on reads (GET list, GET id); 403 on writes (POST, PATCH, DELETE).
    - ADMIN: 200/201 on all operations (GET, POST, PATCH, DELETE).
    - Unauthenticated: 401 on all operations.
    """
    admin_h = _create_auth_headers(admin_user)

    create_resp = client.post(
        "/api/v1/product-categories",
        json={"name": f"Matrix Cat {uuid.uuid4().hex[:4]}"},
        headers=admin_h,
    )
    assert create_resp.status_code == 201
    cat_id = create_resp.json()["id"]

    manager_user = User(
        name="Catalog Mgr",
        email=f"cmgr-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.SALES_MANAGER,
        is_active=True,
    )
    rep_user = User(
        name="Catalog Rep",
        email=f"crep-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.SALES_REP,
        is_active=True,
    )
    finance_user = User(
        name="Catalog Finance",
        email=f"cfin-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.FINANCE_OPERATIONS,
        is_active=True,
    )
    cust_user = User(
        name="Catalog Customer",
        email=f"ccust-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add_all([manager_user, rep_user, finance_user, cust_user])
    db.commit()

    manager_h = _create_auth_headers(manager_user)
    rep_h = _create_auth_headers(rep_user)
    finance_h = _create_auth_headers(finance_user)
    cust_h = _create_auth_headers(cust_user)

    write_payload = {"name": f"Attempt {uuid.uuid4().hex[:4]}"}

    # 1. CUSTOMER: Blocked from all endpoints (403)
    assert client.get("/api/v1/product-categories", headers=cust_h).status_code == 403
    assert client.get(f"/api/v1/product-categories/{cat_id}", headers=cust_h).status_code == 403
    assert client.post("/api/v1/product-categories", json=write_payload, headers=cust_h).status_code == 403
    assert client.patch(f"/api/v1/product-categories/{cat_id}", json=write_payload, headers=cust_h).status_code == 403
    assert client.delete(f"/api/v1/product-categories/{cat_id}", headers=cust_h).status_code == 403

    # 2. Non-Admin internal roles (SALES_REP, SALES_MANAGER, FINANCE_OPERATIONS):
    # Allowed on read (GET list, GET id); Forbidden on write (POST, PATCH, DELETE) because configuration is Admin only
    for role_h in [rep_h, manager_h, finance_h]:
        assert client.get("/api/v1/product-categories", headers=role_h).status_code == 200
        assert client.get(f"/api/v1/product-categories/{cat_id}", headers=role_h).status_code == 200
        assert client.post("/api/v1/product-categories", json=write_payload, headers=role_h).status_code == 403
        assert client.patch(f"/api/v1/product-categories/{cat_id}", json=write_payload, headers=role_h).status_code == 403
        assert client.delete(f"/api/v1/product-categories/{cat_id}", headers=role_h).status_code == 403

    # 3. ADMIN: Allowed on all operations
    assert client.get("/api/v1/product-categories", headers=admin_h).status_code == 200
    assert client.get(f"/api/v1/product-categories/{cat_id}", headers=admin_h).status_code == 200
    admin_created = client.post("/api/v1/product-categories", json={"name": f"Admin Cat {uuid.uuid4().hex[:4]}"}, headers=admin_h)
    assert admin_created.status_code == 201
    created_id = admin_created.json()["id"]
    assert client.patch(f"/api/v1/product-categories/{created_id}", json={"description": "Admin updated"}, headers=admin_h).status_code == 200
    assert client.delete(f"/api/v1/product-categories/{created_id}", headers=admin_h).status_code == 200

    # 4. Unauthenticated: 401 on all endpoints
    assert client.get("/api/v1/product-categories").status_code == 401
    assert client.get(f"/api/v1/product-categories/{cat_id}").status_code == 401
    assert client.post("/api/v1/product-categories", json=write_payload).status_code == 401
    assert client.patch(f"/api/v1/product-categories/{cat_id}", json=write_payload).status_code == 401
    assert client.delete(f"/api/v1/product-categories/{cat_id}").status_code == 401
