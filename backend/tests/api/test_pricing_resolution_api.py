"""Tests for Authoritative Pricing Resolution (POST /api/v1/pricing/resolve)."""

from __future__ import annotations

import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import create_access_token, hash_password
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.price_list import PriceList
from app.models.price_list_item import PriceListItem
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_variant import ProductVariant
from app.models.user import User


def _create_auth_headers(user: User) -> dict:
    """Generate Authorization header for a given user."""
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sales_manager_user(db: Session) -> User:
    """Create a SALES_MANAGER user."""
    user = User(
        name="Sales Manager",
        email=f"sm-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.SALES_MANAGER,
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
        name="Customer User",
        email=f"customer-{uuid.uuid4().hex[:6]}@example.com",
        password_hash=hash_password("Password123!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def active_tier(db: Session) -> CustomerTier:
    """Create an active customer tier."""
    tier = CustomerTier(
        name=f"Platinum Tier-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("25.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


@pytest.fixture
def inactive_tier(db: Session) -> CustomerTier:
    """Create an inactive customer tier."""
    tier = CustomerTier(
        name=f"Deprecated Tier-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("5.00"),
        is_active=False,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


@pytest.fixture
def active_customer(db: Session, active_tier: CustomerTier) -> Customer:
    """Create an active customer belonging to active_tier."""
    customer = Customer(
        name="Acme Corp",
        email=f"contact-{uuid.uuid4().hex[:6]}@acme.local",
        customer_tier_id=active_tier.id,
        is_active=True,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@pytest.fixture
def inactive_customer(db: Session, active_tier: CustomerTier) -> Customer:
    """Create an inactive customer."""
    customer = Customer(
        name="Inactive Corp",
        email=f"contact-{uuid.uuid4().hex[:6]}@inactive.local",
        customer_tier_id=active_tier.id,
        is_active=False,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@pytest.fixture
def active_product(db: Session) -> Product:
    """Create an active product."""
    cat = ProductCategory(name=f"HardwareCat-{uuid.uuid4().hex[:6]}", is_active=True)
    db.add(cat)
    db.commit()
    db.refresh(cat)

    prod = Product(
        category_id=cat.id,
        name=f"Core Server-{uuid.uuid4().hex[:6]}",
        sku=f"CORE-{uuid.uuid4().hex[:6].upper()}",
        unit="units",
        base_price=Decimal("1200.00"),
        cost_price=Decimal("800.00"),
        tax_rate=Decimal("15.00"),
        is_active=True,
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


@pytest.fixture
def inactive_product(db: Session) -> Product:
    """Create an inactive product."""
    cat = ProductCategory(name=f"OldCat-{uuid.uuid4().hex[:6]}", is_active=True)
    db.add(cat)
    db.commit()
    db.refresh(cat)

    prod = Product(
        category_id=cat.id,
        name=f"Old Server-{uuid.uuid4().hex[:6]}",
        sku=f"OLD-{uuid.uuid4().hex[:6].upper()}",
        unit="units",
        base_price=Decimal("500.00"),
        cost_price=Decimal("300.00"),
        tax_rate=Decimal("10.00"),
        is_active=False,
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


@pytest.fixture
def active_variant(db: Session, active_product: Product) -> ProductVariant:
    """Create an active variant for active_product."""
    var = ProductVariant(
        product_id=active_product.id,
        attribute_name="RAM",
        attribute_value="64GB",
        extra_price=Decimal("250.00"),
        is_active=True,
    )
    db.add(var)
    db.commit()
    db.refresh(var)
    return var


@pytest.fixture
def inactive_variant(db: Session, active_product: Product) -> ProductVariant:
    """Create an inactive variant for active_product."""
    var = ProductVariant(
        product_id=active_product.id,
        attribute_name="RAM",
        attribute_value="128GB",
        extra_price=Decimal("500.00"),
        is_active=False,
    )
    db.add(var)
    db.commit()
    db.refresh(var)
    return var


# ============================================================================
# RESOLUTION PATH TESTS
# ============================================================================


def test_resolve_base_catalog_product_only(
    client: TestClient, test_user: User, active_product: Product
):
    """Fallback to base catalog when no price lists exist."""
    headers = _create_auth_headers(test_user)
    resp = client.post(
        "/api/v1/pricing/resolve",
        json={"product_id": str(active_product.id), "currency": "USD"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_id"] == str(active_product.id)
    assert data["variant_id"] is None
    assert data["price_list_id"] is None
    assert data["currency"] == "USD"
    assert Decimal(str(data["base_price"])) == active_product.base_price
    assert Decimal(str(data["variant_extra_price"])) == Decimal("0.00")
    assert Decimal(str(data["resolved_unit_price"])) == active_product.base_price
    assert Decimal(str(data["cost_price"])) == active_product.cost_price
    assert data["pricing_source"] == "BASE_CATALOG"


def test_resolve_base_catalog_with_variant(
    client: TestClient,
    test_user: User,
    active_product: Product,
    active_variant: ProductVariant,
):
    """Base catalog price adds variant extra price when no price list matches."""
    headers = _create_auth_headers(test_user)
    resp = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(active_product.id),
            "variant_id": str(active_variant.id),
            "currency": "USD",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["variant_id"] == str(active_variant.id)
    assert Decimal(str(data["base_price"])) == active_product.base_price
    assert Decimal(str(data["variant_extra_price"])) == active_variant.extra_price
    expected_total = active_product.base_price + active_variant.extra_price
    assert Decimal(str(data["resolved_unit_price"])) == expected_total
    assert data["pricing_source"] == "BASE_CATALOG"


def test_resolve_general_price_list_product_override(
    client: TestClient, admin_user: User, test_user: User, active_product: Product
):
    """General active price list product override is used over base catalog."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    # 1. Create general USD price list
    pl = client.post(
        "/api/v1/price-lists",
        json={"name": "General USD PL", "currency": "USD"},
        headers=admin_h,
    ).json()

    # 2. Add product override
    client.post(
        f"/api/v1/price-lists/{pl['id']}/items",
        json={"product_id": str(active_product.id), "price": "1050.00"},
        headers=admin_h,
    )

    # 3. Resolve price
    resp = client.post(
        "/api/v1/pricing/resolve",
        json={"product_id": str(active_product.id), "currency": "USD"},
        headers=rep_h,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["price_list_id"] == pl["id"]
    assert Decimal(str(data["base_price"])) == Decimal("1050.00")
    assert Decimal(str(data["resolved_unit_price"])) == Decimal("1050.00")
    assert Decimal(str(data["variant_extra_price"])) == Decimal("0.00")
    assert data["pricing_source"] == "PRICE_LIST"


def test_resolve_general_price_list_product_override_with_variant(
    client: TestClient,
    admin_user: User,
    test_user: User,
    active_product: Product,
    active_variant: ProductVariant,
):
    """When price list item has product-level override, variant extra price is added."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    # General price list with product-level override ($1050.00)
    pl = client.post(
        "/api/v1/price-lists",
        json={"name": "General USD PL 2", "currency": "USD"},
        headers=admin_h,
    ).json()

    client.post(
        f"/api/v1/price-lists/{pl['id']}/items",
        json={"product_id": str(active_product.id), "price": "1050.00"},
        headers=admin_h,
    )

    # Resolve with variant (extra = $250.00)
    resp = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(active_product.id),
            "variant_id": str(active_variant.id),
            "currency": "USD",
        },
        headers=rep_h,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["price_list_id"] == pl["id"]
    assert Decimal(str(data["base_price"])) == Decimal("1050.00")
    assert Decimal(str(data["variant_extra_price"])) == Decimal("250.00")
    assert Decimal(str(data["resolved_unit_price"])) == Decimal("1300.00")
    assert data["pricing_source"] == "PRICE_LIST"


def test_resolve_variant_specific_price_list_item(
    client: TestClient,
    admin_user: User,
    test_user: User,
    active_product: Product,
    active_variant: ProductVariant,
):
    """Variant-specific price list override is all-inclusive (no extra added on top)."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    pl = client.post(
        "/api/v1/price-lists",
        json={"name": "Variant Specific PL", "currency": "USD"},
        headers=admin_h,
    ).json()

    # Add product-level override ($1100.00) AND variant-specific override ($1275.00)
    client.post(
        f"/api/v1/price-lists/{pl['id']}/items",
        json={"product_id": str(active_product.id), "price": "1100.00"},
        headers=admin_h,
    )
    client.post(
        f"/api/v1/price-lists/{pl['id']}/items",
        json={
            "product_id": str(active_product.id),
            "variant_id": str(active_variant.id),
            "price": "1275.00",
        },
        headers=admin_h,
    )

    # Resolve with variant -> matches variant-specific override
    resp = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(active_product.id),
            "variant_id": str(active_variant.id),
            "currency": "USD",
        },
        headers=rep_h,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["price_list_id"] == pl["id"]
    assert Decimal(str(data["base_price"])) == Decimal("1275.00")
    assert Decimal(str(data["variant_extra_price"])) == Decimal("0.00")
    assert Decimal(str(data["resolved_unit_price"])) == Decimal("1275.00")
    assert data["pricing_source"] == "PRICE_LIST"


def test_resolve_customer_tier_pricing(
    client: TestClient,
    admin_user: User,
    test_user: User,
    active_tier: CustomerTier,
    active_customer: Customer,
    active_product: Product,
):
    """Customer-tier price list takes precedence over general price list."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    # General PL ($1100.00)
    client.post(
        "/api/v1/price-lists",
        json={"name": "General List", "currency": "USD"},
        headers=admin_h,
    )

    # Platinum Tier PL ($950.00)
    tier_pl = client.post(
        "/api/v1/price-lists",
        json={
            "name": "Platinum Tier List",
            "currency": "USD",
            "customer_tier_id": str(active_tier.id),
        },
        headers=admin_h,
    ).json()

    client.post(
        f"/api/v1/price-lists/{tier_pl['id']}/items",
        json={"product_id": str(active_product.id), "price": "950.00"},
        headers=admin_h,
    )

    # 1. Resolve passing customer_id (customer has active_tier)
    resp_cust = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(active_product.id),
            "customer_id": str(active_customer.id),
            "currency": "USD",
        },
        headers=rep_h,
    )
    assert resp_cust.status_code == 200
    assert resp_cust.json()["price_list_id"] == tier_pl["id"]
    assert Decimal(str(resp_cust.json()["resolved_unit_price"])) == Decimal("950.00")

    # 2. Resolve passing customer_tier_id explicitly
    resp_tier = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(active_product.id),
            "customer_tier_id": str(active_tier.id),
            "currency": "USD",
        },
        headers=rep_h,
    )
    assert resp_tier.status_code == 200
    assert resp_tier.json()["price_list_id"] == tier_pl["id"]
    assert Decimal(str(resp_tier.json()["resolved_unit_price"])) == Decimal("950.00")


def test_resolve_currency_specific_pricing(
    client: TestClient,
    admin_user: User,
    test_user: User,
    active_product: Product,
):
    """Currency matching: requested EUR resolves to EUR price list."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    eur_pl = client.post(
        "/api/v1/price-lists",
        json={"name": "European Retail", "currency": "EUR"},
        headers=admin_h,
    ).json()

    client.post(
        f"/api/v1/price-lists/{eur_pl['id']}/items",
        json={"product_id": str(active_product.id), "price": "1000.00"},
        headers=admin_h,
    )

    resp = client.post(
        "/api/v1/pricing/resolve",
        json={"product_id": str(active_product.id), "currency": "EUR"},
        headers=rep_h,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["price_list_id"] == eur_pl["id"]
    assert data["currency"] == "EUR"
    assert Decimal(str(data["resolved_unit_price"])) == Decimal("1000.00")


def test_resolve_explicit_price_list_override(
    client: TestClient,
    admin_user: User,
    test_user: User,
    active_product: Product,
):
    """Specifying price_list_id directly forces resolution against that specific list."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    special_pl = client.post(
        "/api/v1/price-lists",
        json={"name": "Special Event List", "currency": "USD"},
        headers=admin_h,
    ).json()

    client.post(
        f"/api/v1/price-lists/{special_pl['id']}/items",
        json={"product_id": str(active_product.id), "price": "850.00"},
        headers=admin_h,
    )

    resp = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(active_product.id),
            "price_list_id": special_pl["id"],
            "currency": "USD",
        },
        headers=rep_h,
    )
    assert resp.status_code == 200
    assert resp.json()["price_list_id"] == special_pl["id"]
    assert Decimal(str(resp.json()["resolved_unit_price"])) == Decimal("850.00")


# ============================================================================
# INACTIVE & ERROR HANDLING TESTS
# ============================================================================


def test_resolve_inactive_price_list_ignored(
    client: TestClient,
    admin_user: User,
    test_user: User,
    active_product: Product,
):
    """Inactive price lists are ignored during automatic resolution."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    # Create inactive price list
    inactive_pl = client.post(
        "/api/v1/price-lists",
        json={"name": "Old Deactivated List", "currency": "USD", "is_active": False},
        headers=admin_h,
    ).json()

    client.post(
        f"/api/v1/price-lists/{inactive_pl['id']}/items",
        json={"product_id": str(active_product.id), "price": "500.00"},
        headers=admin_h,
    )

    # Resolving should ignore inactive list and fall back to base catalog
    resp = client.post(
        "/api/v1/pricing/resolve",
        json={"product_id": str(active_product.id), "currency": "USD"},
        headers=rep_h,
    )
    assert resp.status_code == 200
    assert resp.json()["price_list_id"] is None
    assert resp.json()["pricing_source"] == "BASE_CATALOG"
    assert Decimal(str(resp.json()["resolved_unit_price"])) == active_product.base_price


def test_resolve_explicit_inactive_price_list_fails(
    client: TestClient,
    admin_user: User,
    test_user: User,
    active_product: Product,
):
    """Passing an explicit inactive price_list_id raises 400."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    inactive_pl = client.post(
        "/api/v1/price-lists",
        json={"name": "Explicit Inactive", "currency": "USD", "is_active": False},
        headers=admin_h,
    ).json()

    resp = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(active_product.id),
            "price_list_id": inactive_pl["id"],
            "currency": "USD",
        },
        headers=rep_h,
    )
    assert resp.status_code == 400
    assert "inactive" in resp.json()["detail"]


def test_resolve_explicit_price_list_missing_item(
    client: TestClient,
    admin_user: User,
    test_user: User,
    active_product: Product,
):
    """Specifying an explicit price list that lacks pricing for the product raises 404."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    empty_pl = client.post(
        "/api/v1/price-lists",
        json={"name": "Empty Price List", "currency": "USD"},
        headers=admin_h,
    ).json()

    resp = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(active_product.id),
            "price_list_id": empty_pl["id"],
            "currency": "USD",
        },
        headers=rep_h,
    )
    assert resp.status_code == 404
    assert "item found" in resp.json()["detail"]


def test_resolve_currency_mismatch_with_explicit_price_list(
    client: TestClient,
    admin_user: User,
    test_user: User,
    active_product: Product,
):
    """Passing explicit price list with conflicting currency raises 400."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    eur_pl = client.post(
        "/api/v1/price-lists",
        json={"name": "EUR Only PL", "currency": "EUR"},
        headers=admin_h,
    ).json()

    resp = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(active_product.id),
            "price_list_id": eur_pl["id"],
            "currency": "USD",
        },
        headers=rep_h,
    )
    assert resp.status_code == 400
    assert "does not match" in resp.json()["detail"]


def test_resolve_invalid_or_inactive_entities(
    client: TestClient,
    test_user: User,
    active_product: Product,
    inactive_product: Product,
    inactive_variant: ProductVariant,
    inactive_customer: Customer,
    inactive_tier: CustomerTier,
    db: Session,
):
    """Verify validation on missing/inactive products, variants, customers, and customer tiers."""
    headers = _create_auth_headers(test_user)

    # 1. Non-existent product -> 404
    assert (
        client.post(
            "/api/v1/pricing/resolve",
            json={"product_id": str(uuid.uuid4()), "currency": "USD"},
            headers=headers,
        ).status_code
        == 404
    )

    # 2. Inactive product -> 400
    p_inact = client.post(
        "/api/v1/pricing/resolve",
        json={"product_id": str(inactive_product.id), "currency": "USD"},
        headers=headers,
    )
    assert p_inact.status_code == 400
    assert "inactive" in p_inact.json()["detail"]

    # 3. Non-existent variant -> 404
    v_missing = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(active_product.id),
            "variant_id": str(uuid.uuid4()),
            "currency": "USD",
        },
        headers=headers,
    )
    assert v_missing.status_code == 404

    # 4. Inactive variant -> 400
    v_inact = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(active_product.id),
            "variant_id": str(inactive_variant.id),
            "currency": "USD",
        },
        headers=headers,
    )
    assert v_inact.status_code == 400
    assert "inactive" in v_inact.json()["detail"]

    # 5. Variant belonging to different product -> 400
    cat = ProductCategory(name=f"OtherCat-{uuid.uuid4().hex[:6]}", is_active=True)
    db.add(cat)
    db.commit()
    prod2 = Product(
        category_id=cat.id,
        name="Different Prod",
        sku=f"DIFF-{uuid.uuid4().hex[:6]}",
        unit="units",
        base_price=Decimal("100.00"),
        cost_price=Decimal("50.00"),
        tax_rate=Decimal("5.00"),
    )
    db.add(prod2)
    db.commit()
    v_diff = ProductVariant(
        product_id=prod2.id,
        attribute_name="Color",
        attribute_value="Blue",
        extra_price=Decimal("10.00"),
    )
    db.add(v_diff)
    db.commit()

    v_mismatch = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(active_product.id),
            "variant_id": str(v_diff.id),
            "currency": "USD",
        },
        headers=headers,
    )
    assert v_mismatch.status_code == 400
    assert "belong" in v_mismatch.json()["detail"]

    # 6. Inactive customer -> 400
    c_inact = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(active_product.id),
            "customer_id": str(inactive_customer.id),
            "currency": "USD",
        },
        headers=headers,
    )
    assert c_inact.status_code == 400
    assert "inactive" in c_inact.json()["detail"]

    # 7. Inactive customer tier -> 400
    t_inact = client.post(
        "/api/v1/pricing/resolve",
        json={
            "product_id": str(active_product.id),
            "customer_tier_id": str(inactive_tier.id),
            "currency": "USD",
        },
        headers=headers,
    )
    assert t_inact.status_code == 400
    assert "inactive" in t_inact.json()["detail"]


def test_resolve_client_supplied_price_is_ignored(
    client: TestClient, test_user: User, active_product: Product
):
    """Frontend-supplied price/unit_price fields are completely untrusted and ignored."""
    headers = _create_auth_headers(test_user)
    malicious_payload = {
        "product_id": str(active_product.id),
        "currency": "USD",
        "price": "0.01",
        "resolved_unit_price": "0.01",
        "unit_price": "0.01",
    }
    resp = client.post("/api/v1/pricing/resolve", json=malicious_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    # Must equal active_product.base_price ($1200.00), NOT $0.01
    assert Decimal(str(data["resolved_unit_price"])) == active_product.base_price
    assert Decimal(str(data["resolved_unit_price"])) != Decimal("0.01")


def test_resolve_pricing_authorization(
    client: TestClient,
    test_user: User,
    sales_manager_user: User,
    customer_user: User,
    active_product: Product,
):
    """Verify RBAC: 401 unauthenticated, 403 customer, 200 internal staff roles."""
    rep_h = _create_auth_headers(test_user)
    sm_h = _create_auth_headers(sales_manager_user)
    cust_h = _create_auth_headers(customer_user)
    payload = {"product_id": str(active_product.id), "currency": "USD"}

    # 1. Unauthenticated -> 401
    assert client.post("/api/v1/pricing/resolve", json=payload).status_code == 401

    # 2. Customer user (forbidden) -> 403
    assert client.post("/api/v1/pricing/resolve", json=payload, headers=cust_h).status_code == 403

    # 3. Sales rep -> 200
    assert client.post("/api/v1/pricing/resolve", json=payload, headers=rep_h).status_code == 200

    # 4. Sales manager -> 200
    assert client.post("/api/v1/pricing/resolve", json=payload, headers=sm_h).status_code == 200
