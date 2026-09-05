"""End-to-end integration and verification tests for the Catalog module."""

from __future__ import annotations

import uuid
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import create_access_token
from app.main import app
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_variant import ProductVariant
from app.models.user import User


def _create_auth_headers(user: User) -> dict:
    """Helper to generate Authorization header for a given user."""
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


def test_catalog_router_endpoint_inventory(client: TestClient):
    """
    Step 16 Verification:
    Verify that all 15 Catalog endpoints are registered without duplicates and
    with the expected HTTP methods and URL paths under /api/v1.
    """
    expected_endpoints = {
        ("GET", "/api/v1/product-categories"),
        ("POST", "/api/v1/product-categories"),
        ("GET", "/api/v1/product-categories/{id}"),
        ("PATCH", "/api/v1/product-categories/{id}"),
        ("DELETE", "/api/v1/product-categories/{id}"),
        ("GET", "/api/v1/products"),
        ("POST", "/api/v1/products"),
        ("GET", "/api/v1/products/{id}"),
        ("PATCH", "/api/v1/products/{id}"),
        ("DELETE", "/api/v1/products/{id}"),
        ("POST", "/api/v1/products/{product_id}/variants"),
        ("GET", "/api/v1/products/{id}/variants"),
        ("GET", "/api/v1/variants/{id}"),
        ("PATCH", "/api/v1/variants/{id}"),
        ("DELETE", "/api/v1/variants/{id}"),
    }

    openapi_paths = app.openapi()["paths"]
    registered_endpoints = set()
    for path, path_item in openapi_paths.items():
        for method in ["get", "post", "patch", "delete"]:
            if method in path_item:
                registered_endpoints.add((method.upper(), path))

    for method, path in expected_endpoints:
        assert (method, path) in registered_endpoints, (
            f"Missing route: {method} {path}"
        )


def test_end_to_end_catalog_lifecycle(
    client: TestClient, admin_user: User, test_user: User
):
    """
    Step 19 Verification:
    Exercise complete lifecycle across Category -> Product -> Variant.
    - Admin creates category
    - Admin creates product linked to category
    - Admin creates two variants linked to product
    - Sales Rep views product details (verifying joined category)
    - Sales Rep lists product variants
    - Admin deactivates one variant (verifying filter returns active only)
    - Inactive constraints: cannot add product to inactive category, cannot add variant to inactive product
    """
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    # 1. Admin creates Category
    cat_resp = client.post(
        "/api/v1/product-categories",
        json={"name": "Network Equipment", "description": "Switches, routers, and gateways"},
        headers=admin_h,
    )
    assert cat_resp.status_code == 201
    cat_id = cat_resp.json()["id"]

    # 2. Admin creates Product linked to Category
    sku_switch = f"SW-L3-{uuid.uuid4().hex[:4].upper()}"
    prod_resp = client.post(
        "/api/v1/products",
        json={
            "category_id": cat_id,
            "name": "24-Port Managed Switch",
            "description": "Layer 3 Gigabit Managed Switch",
            "sku": sku_switch,
            "unit": "units",
            "base_price": "850.00",
            "cost_price": "520.00",
            "tax_rate": "18.00",
            "is_subscription": False,
        },
        headers=admin_h,
    )
    assert prod_resp.status_code == 201
    prod_id = prod_resp.json()["id"]

    # 3. Admin creates two Variants for the Product
    var1_resp = client.post(
        f"/api/v1/products/{prod_id}/variants",
        json={
            "attribute_name": "Power Supply",
            "attribute_value": "AC Dual Power",
            "extra_price": "150.00",
            "sku": f"{sku_switch}-AC2",
        },
        headers=admin_h,
    )
    assert var1_resp.status_code == 201
    var1_id = var1_resp.json()["id"]

    var2_resp = client.post(
        f"/api/v1/products/{prod_id}/variants",
        json={
            "attribute_name": "Power Supply",
            "attribute_value": "DC 48V Power",
            "extra_price": "180.00",
            "sku": f"{sku_switch}-DC",
        },
        headers=admin_h,
    )
    assert var2_resp.status_code == 201
    var2_id = var2_resp.json()["id"]

    # 4. Sales Rep queries Product details (verifies nested category relationship)
    detail_resp = client.get(f"/api/v1/products/{prod_id}", headers=rep_h)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == prod_id
    assert detail["name"] == "24-Port Managed Switch"
    assert detail["category"] is not None
    assert detail["category"]["id"] == cat_id
    assert detail["category"]["name"] == "Network Equipment"

    # 5. Sales Rep queries Variants of the Product
    vars_resp = client.get(f"/api/v1/products/{prod_id}/variants", headers=rep_h)
    assert vars_resp.status_code == 200
    variants = vars_resp.json()
    assert len(variants) == 2
    var_values = {v["attribute_value"] for v in variants}
    assert var_values == {"AC Dual Power", "DC 48V Power"}

    # 6. Admin deactivates second Variant
    del_var_resp = client.delete(f"/api/v1/variants/{var2_id}", headers=admin_h)
    assert del_var_resp.status_code == 200
    assert del_var_resp.json()["is_active"] is False

    # 7. Sales Rep lists active variants only
    active_vars_resp = client.get(
        f"/api/v1/products/{prod_id}/variants?is_active=true",
        headers=rep_h,
    )
    assert active_vars_resp.status_code == 200
    active_variants = active_vars_resp.json()
    assert len(active_variants) == 1
    assert active_variants[0]["id"] == var1_id

    # 8. Admin deactivates Category
    del_cat_resp = client.delete(f"/api/v1/product-categories/{cat_id}", headers=admin_h)
    assert del_cat_resp.status_code == 200
    assert del_cat_resp.json()["is_active"] is False

    # 9. Verify cannot create product under inactive category
    fail_prod_resp = client.post(
        "/api/v1/products",
        json={
            "category_id": cat_id,
            "name": "Should Fail Product",
            "sku": f"FAIL-{uuid.uuid4().hex[:4]}",
            "unit": "pcs",
            "base_price": "100.00",
            "cost_price": "50.00",
        },
        headers=admin_h,
    )
    assert fail_prod_resp.status_code == 400
    assert "inactive" in fail_prod_resp.json()["detail"].lower()

    # 10. Admin deactivates Product
    del_prod_resp = client.delete(f"/api/v1/products/{prod_id}", headers=admin_h)
    assert del_prod_resp.status_code == 200
    assert del_prod_resp.json()["is_active"] is False

    # 11. Verify cannot create variant under inactive product
    fail_var_resp = client.post(
        f"/api/v1/products/{prod_id}/variants",
        json={"attribute_name": "Fan", "attribute_value": "Redundant Fan"},
        headers=admin_h,
    )
    assert fail_var_resp.status_code == 400
    assert "inactive" in fail_var_resp.json()["detail"].lower()


def test_cross_module_coexistence(
    client: TestClient, admin_user: User, test_user: User, db: Session
):
    """
    Step 16 & 19 Verification:
    Verify that existing Auth, User, Customer Tier, and Customer APIs remain completely
    functional alongside the newly integrated Catalog module.
    """
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    # 1. Auth check
    me_resp = client.get("/api/v1/auth/me", headers=rep_h)
    assert me_resp.status_code == 200
    assert me_resp.json()["id"] == str(test_user.id)

    # 2. Users check
    users_resp = client.get("/api/v1/users", headers=admin_h)
    assert users_resp.status_code == 200
    assert len(users_resp.json()) >= 2

    # 3. Customer Tier check
    tier = CustomerTier(
        name=f"Gold Tier-{uuid.uuid4().hex[:4]}",
        default_discount_limit=Decimal("15.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)

    tiers_resp = client.get("/api/v1/customer-tiers", headers=rep_h)
    assert tiers_resp.status_code == 200

    # 4. Customer check
    customer = Customer(
        name=f"Enterprise Client-{uuid.uuid4().hex[:4]}",
        email=f"client-{uuid.uuid4().hex[:4]}@example.com",
        customer_tier_id=tier.id,
        is_active=True,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    cust_resp = client.get(f"/api/v1/customers/{customer.id}", headers=rep_h)
    assert cust_resp.status_code == 200
    assert cust_resp.json()["name"] == customer.name
