"""Tests for Price List and Price List Item Management APIs."""

from __future__ import annotations

import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import create_access_token, hash_password
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
        name=f"Gold Tier-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("15.00"),
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
        name=f"Legacy Tier-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("5.00"),
        is_active=False,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


@pytest.fixture
def active_product(db: Session) -> Product:
    """Create an active product."""
    cat = ProductCategory(name=f"Cat-{uuid.uuid4().hex[:6]}", is_active=True)
    db.add(cat)
    db.commit()
    db.refresh(cat)

    prod = Product(
        category_id=cat.id,
        name=f"Standard Server-{uuid.uuid4().hex[:6]}",
        sku=f"SRV-{uuid.uuid4().hex[:6].upper()}",
        unit="units",
        base_price=Decimal("1200.00"),
        cost_price=Decimal("700.00"),
        tax_rate=Decimal("10.00"),
        is_active=True,
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


@pytest.fixture
def inactive_product(db: Session) -> Product:
    """Create an inactive product."""
    cat = ProductCategory(name=f"InactiveCat-{uuid.uuid4().hex[:6]}", is_active=True)
    db.add(cat)
    db.commit()
    db.refresh(cat)

    prod = Product(
        category_id=cat.id,
        name=f"Discontinued Server-{uuid.uuid4().hex[:6]}",
        sku=f"DISC-{uuid.uuid4().hex[:6].upper()}",
        unit="units",
        base_price=Decimal("800.00"),
        cost_price=Decimal("500.00"),
        tax_rate=Decimal("10.00"),
        is_active=False,
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


@pytest.fixture
def product_variants(db: Session, active_product: Product) -> list[ProductVariant]:
    """Create two variants for active_product."""
    v1 = ProductVariant(
        product_id=active_product.id,
        attribute_name="RAM",
        attribute_value="32GB",
        extra_price=Decimal("150.00"),
        is_active=True,
    )
    v2 = ProductVariant(
        product_id=active_product.id,
        attribute_name="RAM",
        attribute_value="64GB",
        extra_price=Decimal("300.00"),
        is_active=True,
    )
    v_inactive = ProductVariant(
        product_id=active_product.id,
        attribute_name="RAM",
        attribute_value="128GB",
        extra_price=Decimal("600.00"),
        is_active=False,
    )
    db.add_all([v1, v2, v_inactive])
    db.commit()
    db.refresh(v1)
    db.refresh(v2)
    db.refresh(v_inactive)
    return [v1, v2, v_inactive]


# ============================================================================
# PRICE LIST TESTS
# ============================================================================


def test_create_price_list_success(
    client: TestClient, admin_user: User, active_tier: CustomerTier
):
    """Verify ADMIN can create price lists with or without customer tier."""
    admin_h = _create_auth_headers(admin_user)

    # 1. With customer tier
    resp = client.post(
        "/api/v1/price-lists",
        json={
            "name": "North America Gold",
            "customer_tier_id": str(active_tier.id),
            "currency": "USD",
            "is_active": True,
        },
        headers=admin_h,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "North America Gold"
    assert data["customer_tier_id"] == str(active_tier.id)
    assert data["currency"] == "USD"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data

    # 2. Without customer tier (general price list), default currency
    resp2 = client.post(
        "/api/v1/price-lists",
        json={"name": "European Standard", "currency": "eur"},
        headers=admin_h,
    )
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["name"] == "European Standard"
    assert data2["currency"] == "EUR"
    assert data2["customer_tier_id"] is None
    assert data2["is_active"] is True


def test_create_price_list_validation_failures(
    client: TestClient, admin_user: User, inactive_tier: CustomerTier
):
    """Verify validation rules: empty name, duplicate name, invalid currency, inactive/invalid tier."""
    admin_h = _create_auth_headers(admin_user)

    # Empty name
    resp = client.post(
        "/api/v1/price-lists",
        json={"name": "   ", "currency": "USD"},
        headers=admin_h,
    )
    assert resp.status_code in (400, 422)

    # Duplicate name
    client.post(
        "/api/v1/price-lists",
        json={"name": "Unique Name", "currency": "USD"},
        headers=admin_h,
    )
    dup_resp = client.post(
        "/api/v1/price-lists",
        json={"name": "Unique Name", "currency": "USD"},
        headers=admin_h,
    )
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"]

    # Invalid currency (too short or numbers)
    curr_resp = client.post(
        "/api/v1/price-lists",
        json={"name": "Invalid Currency", "currency": "US1"},
        headers=admin_h,
    )
    assert curr_resp.status_code in (400, 422)

    # Inactive customer tier
    inactive_resp = client.post(
        "/api/v1/price-lists",
        json={
            "name": "Inactive Tier PL",
            "customer_tier_id": str(inactive_tier.id),
            "currency": "USD",
        },
        headers=admin_h,
    )
    assert inactive_resp.status_code == 400
    assert "inactive" in inactive_resp.json()["detail"]

    # Non-existent customer tier
    non_existent_resp = client.post(
        "/api/v1/price-lists",
        json={
            "name": "Missing Tier PL",
            "customer_tier_id": str(uuid.uuid4()),
            "currency": "USD",
        },
        headers=admin_h,
    )
    assert non_existent_resp.status_code == 404


def test_get_price_list_by_id(client: TestClient, admin_user: User, test_user: User):
    """Verify retrieval by ID returns details, or 404 if not found."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    create_resp = client.post(
        "/api/v1/price-lists",
        json={"name": "Detail Test List", "currency": "USD"},
        headers=admin_h,
    )
    pl_id = create_resp.json()["id"]

    # Retrieval by sales rep
    get_resp = client.get(f"/api/v1/price-lists/{pl_id}", headers=rep_h)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == pl_id
    assert get_resp.json()["name"] == "Detail Test List"

    # Not found
    missing_resp = client.get(f"/api/v1/price-lists/{uuid.uuid4()}", headers=rep_h)
    assert missing_resp.status_code == 404


def test_list_price_lists_filtering(
    client: TestClient, admin_user: User, active_tier: CustomerTier, test_user: User
):
    """Verify list filtering by tier, currency, active status, and pagination."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    client.post(
        "/api/v1/price-lists",
        json={"name": "USD Gold", "currency": "USD", "customer_tier_id": str(active_tier.id)},
        headers=admin_h,
    )
    client.post(
        "/api/v1/price-lists",
        json={"name": "EUR General", "currency": "EUR", "is_active": False},
        headers=admin_h,
    )

    # Filter by currency
    usd_resp = client.get("/api/v1/price-lists?currency=usd", headers=rep_h)
    assert usd_resp.status_code == 200
    assert all(pl["currency"] == "USD" for pl in usd_resp.json())

    # Filter by tier
    tier_resp = client.get(f"/api/v1/price-lists?customer_tier_id={active_tier.id}", headers=rep_h)
    assert tier_resp.status_code == 200
    assert all(pl["customer_tier_id"] == str(active_tier.id) for pl in tier_resp.json())

    # Filter by active
    active_resp = client.get("/api/v1/price-lists?is_active=false", headers=rep_h)
    assert active_resp.status_code == 200
    assert all(pl["is_active"] is False for pl in active_resp.json())


def test_update_price_list(
    client: TestClient, admin_user: User, active_tier: CustomerTier
):
    """Verify PATCH /api/v1/price-lists/{id} updates configuration fields."""
    admin_h = _create_auth_headers(admin_user)

    create_resp = client.post(
        "/api/v1/price-lists",
        json={"name": "Initial Name", "currency": "USD"},
        headers=admin_h,
    )
    pl_id = create_resp.json()["id"]

    # Update name, currency, and tier
    update_resp = client.patch(
        f"/api/v1/price-lists/{pl_id}",
        json={
            "name": "Updated Name",
            "currency": "GBP",
            "customer_tier_id": str(active_tier.id),
        },
        headers=admin_h,
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["name"] == "Updated Name"
    assert data["currency"] == "GBP"
    assert data["customer_tier_id"] == str(active_tier.id)

    # Non-existent price list update
    not_found = client.patch(
        f"/api/v1/price-lists/{uuid.uuid4()}",
        json={"name": "Does Not Matter"},
        headers=admin_h,
    )
    assert not_found.status_code == 404


def test_delete_price_list_deactivates_and_preserves_record(
    client: TestClient, admin_user: User, db: Session
):
    """Verify DELETE deactivates price list without physically deleting the database record."""
    admin_h = _create_auth_headers(admin_user)

    create_resp = client.post(
        "/api/v1/price-lists",
        json={"name": "To Deactivate", "currency": "USD"},
        headers=admin_h,
    )
    pl_id = uuid.UUID(create_resp.json()["id"])

    # Deactivate
    del_resp = client.delete(f"/api/v1/price-lists/{pl_id}", headers=admin_h)
    assert del_resp.status_code == 200
    del_data = del_resp.json()
    assert del_data["is_active"] is False

    # Verify record still exists in the database
    db_pl = db.get(PriceList, pl_id)
    assert db_pl is not None
    assert db_pl.is_active is False
    assert db_pl.name == "To Deactivate"


def test_price_list_authorization(
    client: TestClient,
    admin_user: User,
    sales_manager_user: User,
    test_user: User,
    customer_user: User,
):
    """Verify RBAC: unauthenticated -> 401, customer -> 403, internal staff -> GET only, admin -> mutations."""
    admin_h = _create_auth_headers(admin_user)
    sm_h = _create_auth_headers(sales_manager_user)
    rep_h = _create_auth_headers(test_user)
    cust_h = _create_auth_headers(customer_user)

    # 1. Unauthenticated
    assert client.get("/api/v1/price-lists").status_code == 401
    assert client.post("/api/v1/price-lists", json={"name": "X"}).status_code == 401

    # 2. Customer user (external) -> 403 on everything
    assert client.get("/api/v1/price-lists", headers=cust_h).status_code == 403
    assert client.post("/api/v1/price-lists", json={"name": "X"}, headers=cust_h).status_code == 403

    # 3. Staff read -> 200
    assert client.get("/api/v1/price-lists", headers=rep_h).status_code == 200
    assert client.get("/api/v1/price-lists", headers=sm_h).status_code == 200

    # 4. Staff create/patch/delete -> 403
    create_resp = client.post(
        "/api/v1/price-lists",
        json={"name": "Admin Only PL", "currency": "USD"},
        headers=admin_h,
    )
    pl_id = create_resp.json()["id"]

    assert client.post("/api/v1/price-lists", json={"name": "Rep PL"}, headers=rep_h).status_code == 403
    assert client.patch(f"/api/v1/price-lists/{pl_id}", json={"name": "Rep Patch"}, headers=rep_h).status_code == 403
    assert client.delete(f"/api/v1/price-lists/{pl_id}", headers=rep_h).status_code == 403


# ============================================================================
# PRICE LIST ITEM TESTS
# ============================================================================


def test_price_list_items_crud_success(
    client: TestClient,
    admin_user: User,
    active_product: Product,
    product_variants: list[ProductVariant],
    test_user: User,
    db: Session,
):
    """Verify CRUD workflow for Price List Items (product override, variant override, update, delete)."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    # 1. Create parent Price List
    pl_resp = client.post(
        "/api/v1/price-lists",
        json={"name": "Item Test Price List", "currency": "USD"},
        headers=admin_h,
    )
    pl_id = pl_resp.json()["id"]

    # 2. Add product-level price item (no variant)
    item1_resp = client.post(
        f"/api/v1/price-lists/{pl_id}/items",
        json={"product_id": str(active_product.id), "price": "1100.00"},
        headers=admin_h,
    )
    assert item1_resp.status_code == 201
    item1_data = item1_resp.json()
    assert item1_data["product_id"] == str(active_product.id)
    assert item1_data["variant_id"] is None
    assert Decimal(str(item1_data["price"])) == Decimal("1100.00")
    item1_id = item1_data["id"]

    # 3. Add variant-level price item
    v1 = product_variants[0]
    item2_resp = client.post(
        f"/api/v1/price-lists/{pl_id}/items",
        json={
            "product_id": str(active_product.id),
            "variant_id": str(v1.id),
            "price": "1250.00",
        },
        headers=admin_h,
    )
    assert item2_resp.status_code == 201
    item2_data = item2_resp.json()
    assert item2_data["variant_id"] == str(v1.id)
    assert Decimal(str(item2_data["price"])) == Decimal("1250.00")
    item2_id = item2_data["id"]

    # 4. List items (sales rep can read)
    list_resp = client.get(f"/api/v1/price-lists/{pl_id}/items", headers=rep_h)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 2

    # 5. Patch price list item price
    patch_resp = client.patch(
        f"/api/v1/price-lists/{pl_id}/items/{item1_id}",
        json={"price": "1050.00"},
        headers=admin_h,
    )
    assert patch_resp.status_code == 200
    assert Decimal(str(patch_resp.json()["price"])) == Decimal("1050.00")

    # 6. Delete price list item (removes item from list, parent intact)
    del_resp = client.delete(
        f"/api/v1/price-lists/{pl_id}/items/{item1_id}",
        headers=admin_h,
    )
    assert del_resp.status_code == 204

    # Verify item is removed from database
    assert db.get(PriceListItem, uuid.UUID(item1_id)) is None

    # Parent price list is still active and intact
    pl_db = db.get(PriceList, uuid.UUID(pl_id))
    assert pl_db is not None
    assert pl_db.is_active is True

    # Remaining items list has only item2
    remaining_resp = client.get(f"/api/v1/price-lists/{pl_id}/items", headers=rep_h)
    assert len(remaining_resp.json()) == 1
    assert remaining_resp.json()[0]["id"] == item2_id


def test_create_price_list_item_validation_failures(
    client: TestClient,
    admin_user: User,
    active_product: Product,
    inactive_product: Product,
    product_variants: list[ProductVariant],
    db: Session,
):
    """Verify validation on price list item creation: parent missing, product missing/inactive, variant invalid/mismatched/inactive, duplicate item, negative price."""
    admin_h = _create_auth_headers(admin_user)

    pl_resp = client.post(
        "/api/v1/price-lists",
        json={"name": "Validation PL", "currency": "USD"},
        headers=admin_h,
    )
    pl_id = pl_resp.json()["id"]

    # Parent price list not found
    assert (
        client.post(
            f"/api/v1/price-lists/{uuid.uuid4()}/items",
            json={"product_id": str(active_product.id), "price": "100.00"},
            headers=admin_h,
        ).status_code
        == 404
    )

    # Product not found
    assert (
        client.post(
            f"/api/v1/price-lists/{pl_id}/items",
            json={"product_id": str(uuid.uuid4()), "price": "100.00"},
            headers=admin_h,
        ).status_code
        == 404
    )

    # Inactive product
    inact_resp = client.post(
        f"/api/v1/price-lists/{pl_id}/items",
        json={"product_id": str(inactive_product.id), "price": "100.00"},
        headers=admin_h,
    )
    assert inact_resp.status_code == 400
    assert "inactive" in inact_resp.json()["detail"]

    # Inactive variant
    v_inactive = product_variants[2]  # is_active=False
    inact_v_resp = client.post(
        f"/api/v1/price-lists/{pl_id}/items",
        json={
            "product_id": str(active_product.id),
            "variant_id": str(v_inactive.id),
            "price": "150.00",
        },
        headers=admin_h,
    )
    assert inact_v_resp.status_code == 400
    assert "inactive" in inact_v_resp.json()["detail"]

    # Variant belonging to another product
    cat = ProductCategory(name=f"OtherCat-{uuid.uuid4().hex[:6]}", is_active=True)
    db.add(cat)
    db.commit()
    other_prod = Product(
        category_id=cat.id,
        name="Other Prod",
        sku=f"OTH-{uuid.uuid4().hex[:6]}",
        unit="units",
        base_price=Decimal("50.00"),
        cost_price=Decimal("20.00"),
        tax_rate=Decimal("0.00"),
    )
    db.add(other_prod)
    db.commit()

    other_v = ProductVariant(
        product_id=other_prod.id,
        attribute_name="Color",
        attribute_value="Red",
        extra_price=Decimal("5.00"),
    )
    db.add(other_v)
    db.commit()

    mismatch_resp = client.post(
        f"/api/v1/price-lists/{pl_id}/items",
        json={
            "product_id": str(active_product.id),
            "variant_id": str(other_v.id),
            "price": "150.00",
        },
        headers=admin_h,
    )
    assert mismatch_resp.status_code == 400
    assert "belong" in mismatch_resp.json()["detail"]

    # Negative price
    neg_resp = client.post(
        f"/api/v1/price-lists/{pl_id}/items",
        json={"product_id": str(active_product.id), "price": "-10.00"},
        headers=admin_h,
    )
    assert neg_resp.status_code in (400, 422)

    # Duplicate item in the same price list
    client.post(
        f"/api/v1/price-lists/{pl_id}/items",
        json={"product_id": str(active_product.id), "price": "100.00"},
        headers=admin_h,
    )
    dup_resp = client.post(
        f"/api/v1/price-lists/{pl_id}/items",
        json={"product_id": str(active_product.id), "price": "200.00"},
        headers=admin_h,
    )
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"]


def test_update_and_delete_price_list_item_validation(
    client: TestClient,
    admin_user: User,
    active_product: Product,
    product_variants: list[ProductVariant],
):
    """Verify validation when updating and deleting items."""
    admin_h = _create_auth_headers(admin_user)

    pl1 = client.post(
        "/api/v1/price-lists",
        json={"name": "PL 1", "currency": "USD"},
        headers=admin_h,
    ).json()["id"]

    pl2 = client.post(
        "/api/v1/price-lists",
        json={"name": "PL 2", "currency": "USD"},
        headers=admin_h,
    ).json()["id"]

    item_in_pl1 = client.post(
        f"/api/v1/price-lists/{pl1}/items",
        json={"product_id": str(active_product.id), "price": "100.00"},
        headers=admin_h,
    ).json()["id"]

    # Updating item using wrong price list ID -> 404
    wrong_pl_update = client.patch(
        f"/api/v1/price-lists/{pl2}/items/{item_in_pl1}",
        json={"price": "200.00"},
        headers=admin_h,
    )
    assert wrong_pl_update.status_code == 404

    # Deleting item using wrong price list ID -> 404
    wrong_pl_del = client.delete(
        f"/api/v1/price-lists/{pl2}/items/{item_in_pl1}",
        headers=admin_h,
    )
    assert wrong_pl_del.status_code == 404

    # Updating non-existent item -> 404
    assert (
        client.patch(
            f"/api/v1/price-lists/{pl1}/items/{uuid.uuid4()}",
            json={"price": "500.00"},
            headers=admin_h,
        ).status_code
        == 404
    )


def test_price_list_items_authorization(
    client: TestClient,
    admin_user: User,
    test_user: User,
    customer_user: User,
    active_product: Product,
):
    """Verify RBAC on price list items: 401 unauth, 403 customer, 403 non-admin mutation."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)
    cust_h = _create_auth_headers(customer_user)

    pl_id = client.post(
        "/api/v1/price-lists",
        json={"name": "Auth Item PL", "currency": "USD"},
        headers=admin_h,
    ).json()["id"]

    # 1. Unauthenticated
    assert client.get(f"/api/v1/price-lists/{pl_id}/items").status_code == 401
    assert client.post(f"/api/v1/price-lists/{pl_id}/items", json={}).status_code == 401

    # 2. Customer user (forbidden)
    assert client.get(f"/api/v1/price-lists/{pl_id}/items", headers=cust_h).status_code == 403
    assert (
        client.post(
            f"/api/v1/price-lists/{pl_id}/items",
            json={"product_id": str(active_product.id), "price": "100.00"},
            headers=cust_h,
        ).status_code
        == 403
    )

    # 3. Sales rep can GET items
    assert client.get(f"/api/v1/price-lists/{pl_id}/items", headers=rep_h).status_code == 200

    # 4. Sales rep cannot create item
    assert (
        client.post(
            f"/api/v1/price-lists/{pl_id}/items",
            json={"product_id": str(active_product.id), "price": "100.00"},
            headers=rep_h,
        ).status_code
        == 403
    )
