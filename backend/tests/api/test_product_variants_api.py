"""Tests for Product Variant CRUD endpoints and authorization."""

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
from app.models.product_variant import ProductVariant
from app.models.user import User


def _create_auth_headers(user: User) -> dict:
    """Helper to generate Authorization header for a given user."""
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_category(db: Session) -> ProductCategory:
    """Create a default active category for tests."""
    category = ProductCategory(
        name=f"VarCategory-{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def test_product(db: Session, test_category: ProductCategory) -> Product:
    """Create a default active product for variant tests."""
    product = Product(
        category_id=test_category.id,
        name=f"T-Shirt Brand-{uuid.uuid4().hex[:6]}",
        sku=f"TSHIRT-{uuid.uuid4().hex[:6].upper()}",
        unit="pcs",
        base_price=Decimal("25.00"),
        cost_price=Decimal("10.00"),
        tax_rate=Decimal("5.00"),
        is_active=True,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@pytest.fixture
def inactive_product(db: Session, test_category: ProductCategory) -> Product:
    """Create an inactive product for variant tests."""
    product = Product(
        category_id=test_category.id,
        name=f"Legacy Apparel-{uuid.uuid4().hex[:6]}",
        sku=f"LEGACY-{uuid.uuid4().hex[:6].upper()}",
        unit="pcs",
        base_price=Decimal("15.00"),
        cost_price=Decimal("8.00"),
        tax_rate=Decimal("5.00"),
        is_active=False,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def test_create_product_variant_success(
    client: TestClient, admin_user: User, test_product: Product
):
    """Verify ADMIN can create a valid product variant."""
    headers = _create_auth_headers(admin_user)
    payload = {
        "attribute_name": "Size",
        "attribute_value": "XL",
        "extra_price": "5.00",
        "sku": f"TSHIRT-XL-{uuid.uuid4().hex[:4].upper()}",
        "is_active": True,
    }
    response = client.post(
        f"/api/v1/products/{test_product.id}/variants",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] == str(test_product.id)
    assert data["attribute_name"] == "Size"
    assert data["attribute_value"] == "XL"
    assert Decimal(str(data["extra_price"])) == Decimal("5.00")
    assert data["sku"] == payload["sku"]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_product_variant_parent_not_found(
    client: TestClient, admin_user: User
):
    """Verify creating variant for non-existent product returns 404."""
    headers = _create_auth_headers(admin_user)
    fake_product_id = str(uuid.uuid4())
    response = client.post(
        f"/api/v1/products/{fake_product_id}/variants",
        json={"attribute_name": "Size", "attribute_value": "M"},
        headers=headers,
    )
    assert response.status_code == 404
    assert "product not found" in response.json()["detail"].lower()


def test_create_product_variant_inactive_parent_fails(
    client: TestClient, admin_user: User, inactive_product: Product
):
    """Verify creating variant for inactive product returns 400."""
    headers = _create_auth_headers(admin_user)
    response = client.post(
        f"/api/v1/products/{inactive_product.id}/variants",
        json={"attribute_name": "Color", "attribute_value": "Blue"},
        headers=headers,
    )
    assert response.status_code == 400
    assert "inactive" in response.json()["detail"].lower()


def test_create_product_variant_validation_errors(
    client: TestClient, admin_user: User, test_product: Product
):
    """Verify validation on empty attribute_name and attribute_value."""
    headers = _create_auth_headers(admin_user)
    prod_id = str(test_product.id)

    # Missing attribute_name
    resp1 = client.post(
        f"/api/v1/products/{prod_id}/variants",
        json={"attribute_value": "Large"},
        headers=headers,
    )
    assert resp1.status_code == 422

    # Whitespace attribute_name
    resp2 = client.post(
        f"/api/v1/products/{prod_id}/variants",
        json={"attribute_name": "   ", "attribute_value": "Large"},
        headers=headers,
    )
    assert resp2.status_code == 400

    # Whitespace attribute_value
    resp3 = client.post(
        f"/api/v1/products/{prod_id}/variants",
        json={"attribute_name": "Size", "attribute_value": "   "},
        headers=headers,
    )
    assert resp3.status_code == 400


def test_list_product_variants(
    client: TestClient,
    admin_user: User,
    test_user: User,
    test_product: Product,
):
    """Verify listing variants for a product with active filter and pagination."""
    admin_headers = _create_auth_headers(admin_user)
    rep_headers = _create_auth_headers(test_user)
    prod_id = str(test_product.id)

    client.post(
        f"/api/v1/products/{prod_id}/variants",
        json={"attribute_name": "Size", "attribute_value": "Small", "is_active": True},
        headers=admin_headers,
    )
    client.post(
        f"/api/v1/products/{prod_id}/variants",
        json={"attribute_name": "Size", "attribute_value": "Medium", "is_active": False},
        headers=admin_headers,
    )

    # SALES_REP can list variants
    resp = client.get(f"/api/v1/products/{prod_id}/variants", headers=rep_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    values = [v["attribute_value"] for v in data]
    assert "Small" in values
    assert "Medium" in values

    # Filter active only
    resp_act = client.get(
        f"/api/v1/products/{prod_id}/variants?is_active=true",
        headers=rep_headers,
    )
    assert resp_act.status_code == 200
    act_values = [v["attribute_value"] for v in resp_act.json()]
    assert "Small" in act_values
    assert "Medium" not in act_values

    # Listing variants of non-existent product returns 404
    resp_404 = client.get(
        f"/api/v1/products/{uuid.uuid4()}/variants",
        headers=rep_headers,
    )
    assert resp_404.status_code == 404


def test_get_variant_by_id(
    client: TestClient,
    admin_user: User,
    test_user: User,
    test_product: Product,
):
    """Verify retrieving variant details by UUID."""
    admin_headers = _create_auth_headers(admin_user)
    rep_headers = _create_auth_headers(test_user)

    create_resp = client.post(
        f"/api/v1/products/{test_product.id}/variants",
        json={
            "attribute_name": "Color",
            "attribute_value": "Red",
            "extra_price": "2.50",
            "sku": "TSHIRT-RED",
        },
        headers=admin_headers,
    )
    var_id = create_resp.json()["id"]

    # Retrieve by ID
    get_resp = client.get(f"/api/v1/variants/{var_id}", headers=rep_headers)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == var_id
    assert data["attribute_name"] == "Color"
    assert data["attribute_value"] == "Red"
    assert Decimal(str(data["extra_price"])) == Decimal("2.50")
    assert data["sku"] == "TSHIRT-RED"

    # Non-existent ID returns 404
    resp_404 = client.get(f"/api/v1/variants/{uuid.uuid4()}", headers=rep_headers)
    assert resp_404.status_code == 404


def test_update_variant(
    client: TestClient, admin_user: User, test_product: Product
):
    """Verify updating variant attributes, extra_price, SKU, and active status."""
    headers = _create_auth_headers(admin_user)

    create_resp = client.post(
        f"/api/v1/products/{test_product.id}/variants",
        json={"attribute_name": "Pack", "attribute_value": "5-Pack", "extra_price": "10.00"},
        headers=headers,
    )
    var_id = create_resp.json()["id"]

    # Partial update
    patch_resp = client.patch(
        f"/api/v1/variants/{var_id}",
        json={
            "attribute_value": "6-Pack",
            "extra_price": "12.00",
            "sku": "PACK-6",
        },
        headers=headers,
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["attribute_value"] == "6-Pack"
    assert Decimal(str(data["extra_price"])) == Decimal("12.00")
    assert data["sku"] == "PACK-6"

    # Updating non-existent variant returns 404
    resp_404 = client.patch(
        f"/api/v1/variants/{uuid.uuid4()}",
        json={"attribute_name": "Ghost"},
        headers=headers,
    )
    assert resp_404.status_code == 404


def test_delete_variant_logical_deactivation(
    client: TestClient, admin_user: User, test_product: Product, db: Session
):
    """Verify DELETE performs logical deactivation and preserves database record."""
    headers = _create_auth_headers(admin_user)

    create_resp = client.post(
        f"/api/v1/products/{test_product.id}/variants",
        json={"attribute_name": "Material", "attribute_value": "Cotton", "is_active": True},
        headers=headers,
    )
    var_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/variants/{var_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["is_active"] is False

    # Check DB record
    var_in_db = db.get(ProductVariant, uuid.UUID(var_id))
    assert var_in_db is not None
    assert var_in_db.is_active is False

    # Delete non-existent variant returns 404
    resp_404 = client.delete(f"/api/v1/variants/{uuid.uuid4()}", headers=headers)
    assert resp_404.status_code == 404


def test_product_variant_role_authorization_matrix(
    client: TestClient, admin_user: User, test_product: Product, db: Session
):
    """
    Verify role-based authorization matrix:
    - CUSTOMER: 403 on all operations.
    - SALES_REP, SALES_MANAGER, FINANCE_OPERATIONS: 200 on read; 403 on write.
    - ADMIN: 200/201 on all operations.
    - Unauthenticated: 401 on all operations.
    """
    admin_h = _create_auth_headers(admin_user)

    create_resp = client.post(
        f"/api/v1/products/{test_product.id}/variants",
        json={"attribute_name": "Spec", "attribute_value": "Standard"},
        headers=admin_h,
    )
    assert create_resp.status_code == 201
    var_id = create_resp.json()["id"]

    manager_user = User(
        name="Var Mgr",
        email=f"vmgr-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.SALES_MANAGER,
        is_active=True,
    )
    rep_user = User(
        name="Var Rep",
        email=f"vrep-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.SALES_REP,
        is_active=True,
    )
    finance_user = User(
        name="Var Finance",
        email=f"vfin-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.FINANCE_OPERATIONS,
        is_active=True,
    )
    cust_user = User(
        name="Var Customer",
        email=f"vcust-{uuid.uuid4().hex[:6]}@test.local",
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

    prod_id = str(test_product.id)
    write_payload = {"attribute_name": "Spec", "attribute_value": "Custom"}

    # 1. CUSTOMER: 403 on all variant endpoints
    assert client.get(f"/api/v1/products/{prod_id}/variants", headers=cust_h).status_code == 403
    assert client.post(f"/api/v1/products/{prod_id}/variants", json=write_payload, headers=cust_h).status_code == 403
    assert client.get(f"/api/v1/variants/{var_id}", headers=cust_h).status_code == 403
    assert client.patch(f"/api/v1/variants/{var_id}", json={"attribute_value": "Hacked"}, headers=cust_h).status_code == 403
    assert client.delete(f"/api/v1/variants/{var_id}", headers=cust_h).status_code == 403

    # 2. Non-Admin internal roles (SALES_REP, SALES_MANAGER, FINANCE_OPERATIONS):
    # Allowed on read; Forbidden on write
    for role_h in [rep_h, manager_h, finance_h]:
        assert client.get(f"/api/v1/products/{prod_id}/variants", headers=role_h).status_code == 200
        assert client.get(f"/api/v1/variants/{var_id}", headers=role_h).status_code == 200
        assert client.post(f"/api/v1/products/{prod_id}/variants", json=write_payload, headers=role_h).status_code == 403
        assert client.patch(f"/api/v1/variants/{var_id}", json={"attribute_value": "Try"}, headers=role_h).status_code == 403
        assert client.delete(f"/api/v1/variants/{var_id}", headers=role_h).status_code == 403

    # 3. ADMIN: Allowed on all operations
    assert client.get(f"/api/v1/products/{prod_id}/variants", headers=admin_h).status_code == 200
    assert client.get(f"/api/v1/variants/{var_id}", headers=admin_h).status_code == 200
    adm_created = client.post(
        f"/api/v1/products/{prod_id}/variants",
        json={"attribute_name": "Edition", "attribute_value": "Deluxe"},
        headers=admin_h,
    )
    assert adm_created.status_code == 201
    adm_var_id = adm_created.json()["id"]
    assert client.patch(f"/api/v1/variants/{adm_var_id}", json={"extra_price": "20.00"}, headers=admin_h).status_code == 200
    assert client.delete(f"/api/v1/variants/{adm_var_id}", headers=admin_h).status_code == 200

    # 4. Unauthenticated: 401 on all endpoints
    assert client.get(f"/api/v1/products/{prod_id}/variants").status_code == 401
    assert client.post(f"/api/v1/products/{prod_id}/variants", json=write_payload).status_code == 401
    assert client.get(f"/api/v1/variants/{var_id}").status_code == 401
    assert client.patch(f"/api/v1/variants/{var_id}", json={"attribute_value": "No Auth"}).status_code == 401
    assert client.delete(f"/api/v1/variants/{var_id}").status_code == 401
