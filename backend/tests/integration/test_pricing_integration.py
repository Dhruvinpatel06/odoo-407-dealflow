"""End-to-end integration and verification tests for the Pricing module."""

from __future__ import annotations

import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.price_list import PriceList
from app.models.price_list_item import PriceListItem
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_variant import ProductVariant
from app.models.user import User


def _create_auth_headers(user: User) -> dict:
    """Helper to generate Authorization header for a given user."""
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def finance_user(db: Session) -> User:
    """Create a FINANCE_OPERATIONS user."""
    user = User(
        name="Finance Manager",
        email=f"finance-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.FINANCE_OPERATIONS,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def customer_user(db: Session) -> User:
    """Create a CUSTOMER user."""
    user = User(
        name="Portal Customer",
        email=f"customer-{uuid.uuid4().hex[:6]}@partner.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_pricing_router_endpoint_inventory():
    """
    Step 4 Endpoint Review:
    Verify that all 10 Pricing endpoints are registered in OpenAPI paths
    under /api/v1 with correct HTTP methods.
    """
    expected_endpoints = {
        ("GET", "/api/v1/price-lists"),
        ("POST", "/api/v1/price-lists"),
        ("GET", "/api/v1/price-lists/{id}"),
        ("PATCH", "/api/v1/price-lists/{id}"),
        ("DELETE", "/api/v1/price-lists/{id}"),
        ("GET", "/api/v1/price-lists/{id}/items"),
        ("POST", "/api/v1/price-lists/{id}/items"),
        ("PATCH", "/api/v1/price-lists/{id}/items/{item_id}"),
        ("DELETE", "/api/v1/price-lists/{id}/items/{item_id}"),
        ("POST", "/api/v1/pricing/resolve"),
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


def test_end_to_end_pricing_lifecycle(
    client: TestClient, admin_user: User, test_user: User, db: Session
):
    """
    Step 4 Integration Lifecycle:
    Exercises complete integration across:
    - Product Category & Product with Variants
    - Customer Tier & Customer
    - General Price List & Tier-Specific Price List
    - Multi-scenario price resolution
    - Deactivation and record preservation
    """
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    # 1. Setup Category, Product, and Variants
    cat = ProductCategory(name=f"Servers-{uuid.uuid4().hex[:6]}", is_active=True)
    db.add(cat)
    db.commit()

    prod = Product(
        category_id=cat.id,
        name="Enterprise Compute Node",
        sku=f"ECN-{uuid.uuid4().hex[:6].upper()}",
        unit="units",
        base_price=Decimal("2000.00"),
        cost_price=Decimal("1200.00"),
        tax_rate=Decimal("18.00"),
        is_active=True,
    )
    db.add(prod)
    db.commit()

    v_ssd = ProductVariant(
        product_id=prod.id,
        attribute_name="Storage",
        attribute_value="2TB NVMe",
        extra_price=Decimal("400.00"),
        is_active=True,
    )
    v_gpu = ProductVariant(
        product_id=prod.id,
        attribute_name="GPU",
        attribute_value="Dual A100",
        extra_price=Decimal("3000.00"),
        is_active=True,
    )
    db.add_all([v_ssd, v_gpu])
    db.commit()

    # 2. Setup Customer Tier & Customer
    tier = CustomerTier(
        name=f"VIP Tier-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("30.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()

    customer = Customer(
        name="Mega Corp",
        email=f"procurement-{uuid.uuid4().hex[:6]}@megacorp.local",
        customer_tier_id=tier.id,
        is_active=True,
    )
    db.add(customer)
    db.commit()

    # 3. Create General USD Price List
    gen_pl_resp = client.post(
        "/api/v1/price-lists",
        json={"name": "Standard Commercial 2026", "currency": "USD"},
        headers=admin_h,
    )
    assert gen_pl_resp.status_code == 201
    gen_pl_id = gen_pl_resp.json()["id"]

    # Product-level override on General Price List ($1800 instead of $2000)
    client.post(
        f"/api/v1/price-lists/{gen_pl_id}/items",
        json={"product_id": str(prod.id), "price": "1800.00"},
        headers=admin_h,
    )

    # 4. Create VIP Tier USD Price List
    tier_pl_resp = client.post(
        "/api/v1/price-lists",
        json={
            "name": "VIP Enterprise USD",
            "currency": "USD",
            "customer_tier_id": str(tier.id),
        },
        headers=admin_h,
    )
    assert tier_pl_resp.status_code == 201
    tier_pl_id = tier_pl_resp.json()["id"]

    # Product-level override on VIP list ($1600.00)
    client.post(
        f"/api/v1/price-lists/{tier_pl_id}/items",
        json={"product_id": str(prod.id), "price": "1600.00"},
        headers=admin_h,
    )

    # Variant-specific override on VIP list for GPU variant ($4200.00 total)
    client.post(
        f"/api/v1/price-lists/{tier_pl_id}/items",
        json={
            "product_id": str(prod.id),
            "variant_id": str(v_gpu.id),
            "price": "4200.00",
        },
        headers=admin_h,
    )

    # 5. Authoritative Resolution Scenarios

    # Scenario A: Non-tiered user resolving product -> gets General PL price ($1800.00)
    res_gen = client.post(
        "/api/v1/pricing/resolve",
        json={"product_id": str(prod.id), "currency": "USD"},
        headers=rep_h,
    )
    assert res_gen.status_code == 200
    assert res_gen.json()["price_list_id"] == gen_pl_id
    assert Decimal(str(res_gen.json()["resolved_unit_price"])) == Decimal("1800.00")

    # Scenario B: VIP customer resolving product -> gets VIP Tier PL price ($1600.00)
    res_vip = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(prod.id),
            "customer_id": str(customer.id),
            "currency": "USD",
        },
        headers=rep_h,
    )
    assert res_vip.status_code == 200
    assert res_vip.json()["price_list_id"] == tier_pl_id
    assert Decimal(str(res_vip.json()["resolved_unit_price"])) == Decimal("1600.00")

    # Scenario C: VIP customer resolving product with NVMe variant (product override $1600 + extra $400 = $2000)
    res_nvme = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(prod.id),
            "variant_id": str(v_ssd.id),
            "customer_id": str(customer.id),
            "currency": "USD",
        },
        headers=rep_h,
    )
    assert res_nvme.status_code == 200
    assert res_nvme.json()["price_list_id"] == tier_pl_id
    assert Decimal(str(res_nvme.json()["base_price"])) == Decimal("1600.00")
    assert Decimal(str(res_nvme.json()["variant_extra_price"])) == Decimal("400.00")
    assert Decimal(str(res_nvme.json()["resolved_unit_price"])) == Decimal("2000.00")

    # Scenario D: VIP customer resolving GPU variant -> variant-specific override ($4200.00 flat)
    res_gpu = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(prod.id),
            "variant_id": str(v_gpu.id),
            "customer_id": str(customer.id),
            "currency": "USD",
        },
        headers=rep_h,
    )
    assert res_gpu.status_code == 200
    assert res_gpu.json()["price_list_id"] == tier_pl_id
    assert Decimal(str(res_gpu.json()["base_price"])) == Decimal("4200.00")
    assert Decimal(str(res_gpu.json()["variant_extra_price"])) == Decimal("0.00")
    assert Decimal(str(res_gpu.json()["resolved_unit_price"])) == Decimal("4200.00")

    # 6. Deactivation & Fallback Lifecycle
    # Deactivate VIP Price List -> Customer automatically falls back to General PL
    del_tier_pl = client.delete(f"/api/v1/price-lists/{tier_pl_id}", headers=admin_h)
    assert del_tier_pl.status_code == 200
    assert del_tier_pl.json()["is_active"] is False

    # Confirm VIP Price List row is preserved in DB
    db_tier_pl = db.get(PriceList, uuid.UUID(tier_pl_id))
    assert db_tier_pl is not None
    assert db_tier_pl.is_active is False

    # Resolution for VIP customer now falls back to General PL ($1800.00)
    res_after_deact = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(prod.id),
            "customer_id": str(customer.id),
            "currency": "USD",
        },
        headers=rep_h,
    )
    assert res_after_deact.status_code == 200
    assert res_after_deact.json()["price_list_id"] == gen_pl_id
    assert Decimal(str(res_after_deact.json()["resolved_unit_price"])) == Decimal("1800.00")

    # Deactivate General Price List -> Falls back to Base Catalog ($2000.00)
    client.delete(f"/api/v1/price-lists/{gen_pl_id}", headers=admin_h)
    res_base_fallback = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(prod.id),
            "customer_id": str(customer.id),
            "currency": "USD",
        },
        headers=rep_h,
    )
    assert res_base_fallback.status_code == 200
    assert res_base_fallback.json()["price_list_id"] is None
    assert res_base_fallback.json()["pricing_source"] == "BASE_CATALOG"
    assert Decimal(str(res_base_fallback.json()["resolved_unit_price"])) == Decimal("2000.00")


def test_pricing_role_authorization_matrix(
    client: TestClient,
    admin_user: User,
    test_user: User,
    finance_user: User,
    customer_user: User,
    db: Session,
):
    """
    Step 4 Authorization Review:
    Verify exact RBAC matrix across all 10 endpoints:
    - Admin: Full access (create, read, update, delete, resolve).
    - Staff (Sales Rep, Finance): Read and resolve allowed, mutations forbidden (403).
    - Customer: All pricing endpoints forbidden (403).
    - Unauthenticated: All pricing endpoints unauthorized (401).
    """
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)
    fin_h = _create_auth_headers(finance_user)
    cust_h = _create_auth_headers(customer_user)

    # Setup dummy product and price list
    cat = ProductCategory(name=f"AuthCat-{uuid.uuid4().hex[:6]}", is_active=True)
    db.add(cat)
    db.commit()
    prod = Product(
        category_id=cat.id,
        name="Auth Probe",
        sku=f"PRB-{uuid.uuid4().hex[:6]}",
        unit="units",
        base_price=Decimal("100.00"),
        cost_price=Decimal("60.00"),
        tax_rate=Decimal("5.00"),
    )
    db.add(prod)
    db.commit()

    pl = client.post(
        "/api/v1/price-lists",
        json={"name": "Auth Matrix PL", "currency": "USD"},
        headers=admin_h,
    ).json()
    pl_id = pl["id"]

    item = client.post(
        f"/api/v1/price-lists/{pl_id}/items",
        json={"product_id": str(prod.id), "price": "90.00"},
        headers=admin_h,
    ).json()
    item_id = item["id"]

    test_routes = [
        ("GET", "/api/v1/price-lists", None),
        ("POST", "/api/v1/price-lists", {"name": "Test", "currency": "USD"}),
        ("GET", f"/api/v1/price-lists/{pl_id}", None),
        ("PATCH", f"/api/v1/price-lists/{pl_id}", {"name": "PatchTest"}),
        ("DELETE", f"/api/v1/price-lists/{pl_id}", None),
        ("GET", f"/api/v1/price-lists/{pl_id}/items", None),
        ("POST", f"/api/v1/price-lists/{pl_id}/items", {"product_id": str(prod.id), "price": "95.00"}),
        ("PATCH", f"/api/v1/price-lists/{pl_id}/items/{item_id}", {"price": "88.00"}),
        ("DELETE", f"/api/v1/price-lists/{pl_id}/items/{item_id}", None),
        ("POST", "/api/v1/pricing/resolve", {"product_id": str(prod.id), "currency": "USD"}),
    ]

    for method, path, body in test_routes:
        # 1. Unauthenticated -> 401
        res_unauth = client.request(method, path, json=body)
        assert res_unauth.status_code == 401, f"Expected 401 for unauth on {method} {path}"

        # 2. Customer user -> 403
        res_cust = client.request(method, path, json=body, headers=cust_h)
        assert res_cust.status_code == 403, f"Expected 403 for customer on {method} {path}"

        # 3. Staff permissions
        if method in ("GET",) or path == "/api/v1/pricing/resolve":
            # Sales Rep & Finance can read and resolve
            assert client.request(method, path, json=body, headers=rep_h).status_code in (200, 201), (
                f"Sales rep should access {method} {path}"
            )
            assert client.request(method, path, json=body, headers=fin_h).status_code in (200, 201), (
                f"Finance operations should access {method} {path}"
            )
        else:
            # Mutations must be forbidden for non-admin
            assert client.request(method, path, json=body, headers=rep_h).status_code == 403, (
                f"Sales rep should be forbidden on {method} {path}"
            )
            assert client.request(method, path, json=body, headers=fin_h).status_code == 403, (
                f"Finance operations should be forbidden on {method} {path}"
            )
