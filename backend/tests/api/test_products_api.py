"""Tests for Product CRUD endpoints and authorization."""

from __future__ import annotations

import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import create_access_token
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.user import User


def _create_auth_headers(user: User) -> dict:
    """Helper to generate Authorization header for a given user."""
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_category(db: Session) -> ProductCategory:
    """Create a default active product category for tests."""
    category = ProductCategory(
        name=f"Hardware-{uuid.uuid4().hex[:6]}",
        description="Physical devices and hardware",
        is_active=True,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def inactive_category(db: Session) -> ProductCategory:
    """Create an inactive product category for tests."""
    category = ProductCategory(
        name=f"Deprecated-{uuid.uuid4().hex[:6]}",
        description="Deprecated category",
        is_active=False,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def test_create_product_success(
    client: TestClient, admin_user: User, test_category: ProductCategory
):
    """Verify ADMIN can create a valid product with correct attributes and numeric values."""
    headers = _create_auth_headers(admin_user)
    payload = {
        "category_id": str(test_category.id),
        "name": "Enterprise Server Rack",
        "description": "High-density 42U server cabinet",
        "sku": f"SRV-42U-{uuid.uuid4().hex[:4].upper()}",
        "unit": "pcs",
        "base_price": "2500.00",
        "cost_price": "1700.00",
        "tax_rate": "18.00",
        "is_subscription": False,
        "is_active": True,
    }
    response = client.post("/api/v1/products", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Enterprise Server Rack"
    assert data["category_id"] == str(test_category.id)
    assert data["sku"] == payload["sku"]
    assert data["unit"] == "pcs"
    assert Decimal(str(data["base_price"])) == Decimal("2500.00")
    assert Decimal(str(data["cost_price"])) == Decimal("1700.00")
    assert Decimal(str(data["tax_rate"])) == Decimal("18.00")
    assert data["is_subscription"] is False
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_product_duplicate_sku_fails(
    client: TestClient, admin_user: User, test_category: ProductCategory
):
    """Verify creating a product with an existing SKU returns 400 (case-insensitive)."""
    headers = _create_auth_headers(admin_user)
    sku_val = f"SKU-DUP-{uuid.uuid4().hex[:4].upper()}"
    payload = {
        "category_id": str(test_category.id),
        "name": "Product Alpha",
        "sku": sku_val,
        "unit": "pcs",
        "base_price": "100.00",
        "cost_price": "60.00",
        "tax_rate": "5.00",
    }
    resp1 = client.post("/api/v1/products", json=payload, headers=headers)
    assert resp1.status_code == 201

    # Exact duplicate
    resp2 = client.post("/api/v1/products", json=payload, headers=headers)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"].lower()

    # Case-insensitive duplicate
    payload_case = dict(payload)
    payload_case["sku"] = sku_val.lower()
    payload_case["name"] = "Product Beta"
    resp3 = client.post("/api/v1/products", json=payload_case, headers=headers)
    assert resp3.status_code == 400
    assert "already exists" in resp3.json()["detail"].lower()


def test_create_product_invalid_category_fails(
    client: TestClient, admin_user: User, inactive_category: ProductCategory
):
    """Verify assigning nonexistent category returns 404 and inactive category returns 400."""
    headers = _create_auth_headers(admin_user)

    # Nonexistent category
    fake_cat_id = str(uuid.uuid4())
    resp_nonexistent = client.post(
        "/api/v1/products",
        json={
            "category_id": fake_cat_id,
            "name": "Widget X",
            "sku": f"WID-{uuid.uuid4().hex[:4].upper()}",
            "unit": "pcs",
            "base_price": "50.00",
            "cost_price": "30.00",
        },
        headers=headers,
    )
    assert resp_nonexistent.status_code == 404
    assert "category not found" in resp_nonexistent.json()["detail"].lower()

    # Inactive category
    resp_inactive = client.post(
        "/api/v1/products",
        json={
            "category_id": str(inactive_category.id),
            "name": "Widget Inactive",
            "sku": f"WID-INACT-{uuid.uuid4().hex[:4].upper()}",
            "unit": "pcs",
            "base_price": "50.00",
            "cost_price": "30.00",
        },
        headers=headers,
    )
    assert resp_inactive.status_code == 400
    assert "inactive" in resp_inactive.json()["detail"].lower()


def test_create_product_validation_errors(
    client: TestClient, admin_user: User, test_category: ProductCategory
):
    """Verify validation constraints on base_price, cost_price, tax_rate, and strings."""
    headers = _create_auth_headers(admin_user)
    cat_id = str(test_category.id)

    # Negative base_price
    resp_neg_price = client.post(
        "/api/v1/products",
        json={
            "category_id": cat_id,
            "name": "Negative Price Item",
            "sku": f"NEG-P-{uuid.uuid4().hex[:4]}",
            "unit": "pcs",
            "base_price": "-10.00",
            "cost_price": "5.00",
        },
        headers=headers,
    )
    assert resp_neg_price.status_code == 422

    # Negative cost_price
    resp_neg_cost = client.post(
        "/api/v1/products",
        json={
            "category_id": cat_id,
            "name": "Negative Cost Item",
            "sku": f"NEG-C-{uuid.uuid4().hex[:4]}",
            "unit": "pcs",
            "base_price": "10.00",
            "cost_price": "-5.00",
        },
        headers=headers,
    )
    assert resp_neg_cost.status_code == 422

    # Tax rate > 100
    resp_tax = client.post(
        "/api/v1/products",
        json={
            "category_id": cat_id,
            "name": "Excessive Tax Item",
            "sku": f"TAX-E-{uuid.uuid4().hex[:4]}",
            "unit": "pcs",
            "base_price": "10.00",
            "cost_price": "5.00",
            "tax_rate": "150.00",
        },
        headers=headers,
    )
    assert resp_tax.status_code == 422

    # Whitespace-only name
    resp_ws_name = client.post(
        "/api/v1/products",
        json={
            "category_id": cat_id,
            "name": "   ",
            "sku": f"WS-N-{uuid.uuid4().hex[:4]}",
            "unit": "pcs",
            "base_price": "10.00",
            "cost_price": "5.00",
        },
        headers=headers,
    )
    assert resp_ws_name.status_code == 400


def test_list_products_and_filtering(
    client: TestClient,
    admin_user: User,
    test_user: User,
    test_category: ProductCategory,
    db: Session,
):
    """Verify listing products with category filtering, active status filtering, and search."""
    admin_headers = _create_auth_headers(admin_user)
    rep_headers = _create_auth_headers(test_user)

    cat_b = ProductCategory(name=f"Services-{uuid.uuid4().hex[:4]}", is_active=True)
    db.add(cat_b)
    db.commit()
    db.refresh(cat_b)

    # Seed products
    client.post(
        "/api/v1/products",
        json={
            "category_id": str(test_category.id),
            "name": "Laptop Pro 15",
            "sku": f"LAP-PRO-{uuid.uuid4().hex[:4].upper()}",
            "unit": "pcs",
            "base_price": "1200.00",
            "cost_price": "900.00",
            "is_active": True,
        },
        headers=admin_headers,
    )
    client.post(
        "/api/v1/products",
        json={
            "category_id": str(test_category.id),
            "name": "Laptop Pro 13",
            "sku": f"LAP-MINI-{uuid.uuid4().hex[:4].upper()}",
            "unit": "pcs",
            "base_price": "1000.00",
            "cost_price": "750.00",
            "is_active": False,
        },
        headers=admin_headers,
    )
    client.post(
        "/api/v1/products",
        json={
            "category_id": str(cat_b.id),
            "name": "Cloud Maintenance Subscription",
            "sku": f"SUB-MNT-{uuid.uuid4().hex[:4].upper()}",
            "unit": "months",
            "base_price": "300.00",
            "cost_price": "100.00",
            "is_subscription": True,
            "is_active": True,
        },
        headers=admin_headers,
    )

    # SALES_REP can list products
    resp = client.get("/api/v1/products", headers=rep_headers)
    assert resp.status_code == 200
    all_names = [p["name"] for p in resp.json()]
    assert "Laptop Pro 15" in all_names
    assert "Cloud Maintenance Subscription" in all_names

    # Filter by category
    resp_cat = client.get(
        f"/api/v1/products?category_id={test_category.id}", headers=rep_headers
    )
    assert resp_cat.status_code == 200
    cat_names = [p["name"] for p in resp_cat.json()]
    assert "Laptop Pro 15" in cat_names
    assert "Cloud Maintenance Subscription" not in cat_names

    # Filter by is_active=True
    resp_act = client.get(
        f"/api/v1/products?category_id={test_category.id}&is_active=true",
        headers=rep_headers,
    )
    assert resp_act.status_code == 200
    active_names = [p["name"] for p in resp_act.json()]
    assert "Laptop Pro 15" in active_names
    assert "Laptop Pro 13" not in active_names

    # Search by keyword
    resp_search = client.get("/api/v1/products?search=Maintenance", headers=rep_headers)
    assert resp_search.status_code == 200
    search_names = [p["name"] for p in resp_search.json()]
    assert "Cloud Maintenance Subscription" in search_names
    assert "Laptop Pro 15" not in search_names


def test_get_product_by_id(
    client: TestClient, admin_user: User, test_user: User, test_category: ProductCategory
):
    """Verify retrieving product details by UUID returns nested category information."""
    admin_headers = _create_auth_headers(admin_user)
    rep_headers = _create_auth_headers(test_user)

    sku_val = f"PRD-DTL-{uuid.uuid4().hex[:4].upper()}"
    create_resp = client.post(
        "/api/v1/products",
        json={
            "category_id": str(test_category.id),
            "name": "Detailed Router Device",
            "description": "Gigabit fiber router",
            "sku": sku_val,
            "unit": "units",
            "base_price": "450.00",
            "cost_price": "280.00",
            "tax_rate": "12.00",
        },
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    prod_id = create_resp.json()["id"]

    # Retrieve by ID
    get_resp = client.get(f"/api/v1/products/{prod_id}", headers=rep_headers)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == prod_id
    assert data["name"] == "Detailed Router Device"
    assert data["sku"] == sku_val
    assert data["category"] is not None
    assert data["category"]["id"] == str(test_category.id)
    assert data["category"]["name"] == test_category.name

    # Non-existent ID returns 404
    resp_404 = client.get(f"/api/v1/products/{uuid.uuid4()}", headers=rep_headers)
    assert resp_404.status_code == 404


def test_update_product(
    client: TestClient, admin_user: User, test_category: ProductCategory
):
    """Verify updating product attributes, price, tax, and handling SKU conflicts."""
    headers = _create_auth_headers(admin_user)

    sku_orig = f"UPD-A-{uuid.uuid4().hex[:4].upper()}"
    create_resp = client.post(
        "/api/v1/products",
        json={
            "category_id": str(test_category.id),
            "name": "Initial Product Name",
            "sku": sku_orig,
            "unit": "pcs",
            "base_price": "100.00",
            "cost_price": "60.00",
        },
        headers=headers,
    )
    prod_id = create_resp.json()["id"]

    # Partial update: name, price, description
    patch_resp = client.patch(
        f"/api/v1/products/{prod_id}",
        json={
            "name": "Updated Product Name",
            "base_price": "125.00",
            "description": "Updated detailed description",
        },
        headers=headers,
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["name"] == "Updated Product Name"
    assert Decimal(str(updated["base_price"])) == Decimal("125.00")
    assert updated["description"] == "Updated detailed description"
    assert updated["sku"] == sku_orig

    # Create another product to test conflict
    sku_other = f"UPD-B-{uuid.uuid4().hex[:4].upper()}"
    client.post(
        "/api/v1/products",
        json={
            "category_id": str(test_category.id),
            "name": "Other Product",
            "sku": sku_other,
            "unit": "pcs",
            "base_price": "50.00",
            "cost_price": "20.00",
        },
        headers=headers,
    )

    # Conflict on duplicate SKU
    conflict_resp = client.patch(
        f"/api/v1/products/{prod_id}",
        json={"sku": sku_other},
        headers=headers,
    )
    assert conflict_resp.status_code == 400
    assert "already exists" in conflict_resp.json()["detail"].lower()

    # Update non-existent product returns 404
    resp_404 = client.patch(
        f"/api/v1/products/{uuid.uuid4()}",
        json={"name": "Ghost"},
        headers=headers,
    )
    assert resp_404.status_code == 404


def test_delete_product_logical_deactivation(
    client: TestClient, admin_user: User, test_category: ProductCategory, db: Session
):
    """Verify DELETE performs logical deactivation and preserves database record."""
    headers = _create_auth_headers(admin_user)

    create_resp = client.post(
        "/api/v1/products",
        json={
            "category_id": str(test_category.id),
            "name": "Product To Deactivate",
            "sku": f"DEL-{uuid.uuid4().hex[:4].upper()}",
            "unit": "pcs",
            "base_price": "80.00",
            "cost_price": "40.00",
            "is_active": True,
        },
        headers=headers,
    )
    prod_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/products/{prod_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["is_active"] is False

    # Check DB directly: product still exists with is_active = False
    prod_in_db = db.get(Product, uuid.UUID(prod_id))
    assert prod_in_db is not None
    assert prod_in_db.is_active is False

    # Deactivating non-existent product returns 404
    resp_404 = client.delete(f"/api/v1/products/{uuid.uuid4()}", headers=headers)
    assert resp_404.status_code == 404


def test_product_role_authorization_matrix(
    client: TestClient, admin_user: User, test_category: ProductCategory, db: Session
):
    """
    Verify role-based authorization matrix:
    - CUSTOMER: 403 on all operations (GET list, GET id, POST, PATCH, DELETE).
    - SALES_REP, SALES_MANAGER, FINANCE_OPERATIONS: 200 on reads; 403 on writes (Admin only).
    - ADMIN: 200/201 on all operations.
    - Unauthenticated: 401 on all operations.
    """
    admin_h = _create_auth_headers(admin_user)

    create_resp = client.post(
        "/api/v1/products",
        json={
            "category_id": str(test_category.id),
            "name": f"Matrix Product {uuid.uuid4().hex[:4]}",
            "sku": f"MTX-{uuid.uuid4().hex[:4].upper()}",
            "unit": "pcs",
            "base_price": "200.00",
            "cost_price": "120.00",
        },
        headers=admin_h,
    )
    assert create_resp.status_code == 201
    prod_id = create_resp.json()["id"]

    manager_user = User(
        name="Prod Mgr",
        email=f"pmgr-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.SALES_MANAGER,
        is_active=True,
    )
    rep_user = User(
        name="Prod Rep",
        email=f"prep-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.SALES_REP,
        is_active=True,
    )
    finance_user = User(
        name="Prod Finance",
        email=f"pfin-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.FINANCE_OPERATIONS,
        is_active=True,
    )
    cust_user = User(
        name="Prod Customer",
        email=f"pcust-{uuid.uuid4().hex[:6]}@test.local",
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

    write_payload = {
        "category_id": str(test_category.id),
        "name": "Attempted Product",
        "sku": f"ATT-{uuid.uuid4().hex[:4].upper()}",
        "unit": "pcs",
        "base_price": "50.00",
        "cost_price": "25.00",
    }

    # 1. CUSTOMER: Blocked from all product endpoints (403)
    assert client.get("/api/v1/products", headers=cust_h).status_code == 403
    assert client.get(f"/api/v1/products/{prod_id}", headers=cust_h).status_code == 403
    assert client.post("/api/v1/products", json=write_payload, headers=cust_h).status_code == 403
    assert client.patch(f"/api/v1/products/{prod_id}", json={"name": "Cust Try"}, headers=cust_h).status_code == 403
    assert client.delete(f"/api/v1/products/{prod_id}", headers=cust_h).status_code == 403

    # 2. Non-Admin internal roles (SALES_REP, SALES_MANAGER, FINANCE_OPERATIONS):
    # Allowed on read (GET list, GET id); Forbidden on write (POST, PATCH, DELETE)
    for role_h in [rep_h, manager_h, finance_h]:
        assert client.get("/api/v1/products", headers=role_h).status_code == 200
        assert client.get(f"/api/v1/products/{prod_id}", headers=role_h).status_code == 200
        assert client.post("/api/v1/products", json=write_payload, headers=role_h).status_code == 403
        assert client.patch(f"/api/v1/products/{prod_id}", json={"name": "Try"}, headers=role_h).status_code == 403
        assert client.delete(f"/api/v1/products/{prod_id}", headers=role_h).status_code == 403

    # 3. ADMIN: Allowed on all endpoints
    assert client.get("/api/v1/products", headers=admin_h).status_code == 200
    assert client.get(f"/api/v1/products/{prod_id}", headers=admin_h).status_code == 200
    admin_created = client.post(
        "/api/v1/products",
        json={
            "category_id": str(test_category.id),
            "name": "Admin Product",
            "sku": f"ADM-{uuid.uuid4().hex[:4].upper()}",
            "unit": "pcs",
            "base_price": "70.00",
            "cost_price": "35.00",
        },
        headers=admin_h,
    )
    assert admin_created.status_code == 201
    created_id = admin_created.json()["id"]
    assert client.patch(f"/api/v1/products/{created_id}", json={"name": "Admin Modified"}, headers=admin_h).status_code == 200
    assert client.delete(f"/api/v1/products/{created_id}", headers=admin_h).status_code == 200

    # 4. Unauthenticated: 401 on all endpoints
    assert client.get("/api/v1/products").status_code == 401
    assert client.get(f"/api/v1/products/{prod_id}").status_code == 401
    assert client.post("/api/v1/products", json=write_payload).status_code == 401
    assert client.patch(f"/api/v1/products/{prod_id}", json={"name": "No Auth"}).status_code == 401
    assert client.delete(f"/api/v1/products/{prod_id}").status_code == 401
