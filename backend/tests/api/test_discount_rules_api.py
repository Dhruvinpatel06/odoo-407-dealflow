"""Comprehensive API tests for the Discount Rules configuration module."""

from __future__ import annotations

import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import create_access_token, hash_password
from app.models.customer_tier import CustomerTier
from app.models.discount_rule import DiscountRule
from app.models.product_category import ProductCategory
from app.models.user import User


def _create_auth_headers(user: User) -> dict:
    """Helper to generate Authorization header for a given user."""
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def active_tier(db: Session) -> CustomerTier:
    """Fixture providing an active CustomerTier."""
    tier = CustomerTier(
        name=f"Tier-{uuid.uuid4().hex[:6]}",
        description="Active test tier",
        default_discount_limit=Decimal("20.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


@pytest.fixture
def inactive_tier(db: Session) -> CustomerTier:
    """Fixture providing an inactive CustomerTier."""
    tier = CustomerTier(
        name=f"InactiveTier-{uuid.uuid4().hex[:6]}",
        description="Inactive test tier",
        default_discount_limit=Decimal("10.00"),
        is_active=False,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


@pytest.fixture
def active_category(db: Session) -> ProductCategory:
    """Fixture providing an active ProductCategory."""
    category = ProductCategory(
        name=f"Category-{uuid.uuid4().hex[:6]}",
        description="Active test category",
        is_active=True,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def inactive_category(db: Session) -> ProductCategory:
    """Fixture providing an inactive ProductCategory."""
    category = ProductCategory(
        name=f"InactiveCategory-{uuid.uuid4().hex[:6]}",
        description="Inactive test category",
        is_active=False,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def sales_manager_user(db: Session) -> User:
    """Fixture providing an active SALES_MANAGER user."""
    user = User(
        name="Sales Manager",
        email=f"manager-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.SALES_MANAGER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def finance_user(db: Session) -> User:
    """Fixture providing an active FINANCE_OPERATIONS user."""
    user = User(
        name="Finance Ops",
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
    """Fixture providing an external CUSTOMER user."""
    user = User(
        name="Customer Portal User",
        email=f"customer-{uuid.uuid4().hex[:6]}@client.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# =====================================================================
# 1. CREATE ENDPOINT TESTS (POST /api/v1/discount-rules)
# =====================================================================


def test_create_discount_rule_tier_only_success(
    client: TestClient, admin_user: User, active_tier: CustomerTier
):
    """Verify admin can create a discount rule conditioned on customer tier only."""
    headers = _create_auth_headers(admin_user)
    payload = {
        "customer_tier_id": str(active_tier.id),
        "max_discount_percent": "25.00",
        "priority": 1,
        "is_active": True,
    }
    resp = client.post("/api/v1/discount-rules", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["customer_tier_id"] == str(active_tier.id)
    assert data["category_id"] is None
    assert Decimal(str(data["max_discount_percent"])) == Decimal("25.00")
    assert data["priority"] == 1
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_discount_rule_category_only_success(
    client: TestClient, admin_user: User, active_category: ProductCategory
):
    """Verify admin can create a discount rule conditioned on category only."""
    headers = _create_auth_headers(admin_user)
    payload = {
        "category_id": str(active_category.id),
        "max_discount_percent": "15.50",
        "priority": 2,
    }
    resp = client.post("/api/v1/discount-rules", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["customer_tier_id"] is None
    assert data["category_id"] == str(active_category.id)
    assert Decimal(str(data["max_discount_percent"])) == Decimal("15.50")
    assert data["priority"] == 2
    assert data["is_active"] is True


def test_create_discount_rule_both_tier_and_category_success(
    client: TestClient,
    admin_user: User,
    active_tier: CustomerTier,
    active_category: ProductCategory,
):
    """Verify admin can create a discount rule conditioned on both tier and category."""
    headers = _create_auth_headers(admin_user)
    payload = {
        "customer_tier_id": str(active_tier.id),
        "category_id": str(active_category.id),
        "max_discount_percent": "35.00",
        "priority": 10,
    }
    resp = client.post("/api/v1/discount-rules", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["customer_tier_id"] == str(active_tier.id)
    assert data["category_id"] == str(active_category.id)
    assert Decimal(str(data["max_discount_percent"])) == Decimal("35.00")


def test_create_discount_rule_no_conditions_fails(
    client: TestClient, admin_user: User
):
    """Verify creating a discount rule with neither tier nor category fails with 422."""
    headers = _create_auth_headers(admin_user)
    payload = {
        "max_discount_percent": "20.00",
    }
    resp = client.post("/api/v1/discount-rules", json=payload, headers=headers)
    assert resp.status_code == 422


def test_create_discount_rule_invalid_discount_percent_fails(
    client: TestClient, admin_user: User, active_tier: CustomerTier
):
    """Verify discount percentages < 0 or > 100 fail with 422."""
    headers = _create_auth_headers(admin_user)

    # Negative
    resp_neg = client.post(
        "/api/v1/discount-rules",
        json={"customer_tier_id": str(active_tier.id), "max_discount_percent": "-5.00"},
        headers=headers,
    )
    assert resp_neg.status_code == 422

    # Above 100
    resp_over = client.post(
        "/api/v1/discount-rules",
        json={"customer_tier_id": str(active_tier.id), "max_discount_percent": "105.00"},
        headers=headers,
    )
    assert resp_over.status_code == 422


def test_create_discount_rule_invalid_references(
    client: TestClient,
    admin_user: User,
    inactive_tier: CustomerTier,
    inactive_category: ProductCategory,
):
    """Verify non-existent and inactive foreign entity references are rejected."""
    headers = _create_auth_headers(admin_user)
    random_id = str(uuid.uuid4())

    # Non-existent tier -> 404
    resp_no_tier = client.post(
        "/api/v1/discount-rules",
        json={"customer_tier_id": random_id, "max_discount_percent": "10.00"},
        headers=headers,
    )
    assert resp_no_tier.status_code == 404
    assert "tier" in resp_no_tier.json()["detail"].lower()

    # Inactive tier -> 400
    resp_inact_tier = client.post(
        "/api/v1/discount-rules",
        json={"customer_tier_id": str(inactive_tier.id), "max_discount_percent": "10.00"},
        headers=headers,
    )
    assert resp_inact_tier.status_code == 400
    assert "inactive" in resp_inact_tier.json()["detail"].lower()

    # Non-existent category -> 404
    resp_no_cat = client.post(
        "/api/v1/discount-rules",
        json={"category_id": random_id, "max_discount_percent": "10.00"},
        headers=headers,
    )
    assert resp_no_cat.status_code == 404
    assert "category" in resp_no_cat.json()["detail"].lower()

    # Inactive category -> 400
    resp_inact_cat = client.post(
        "/api/v1/discount-rules",
        json={"category_id": str(inactive_category.id), "max_discount_percent": "10.00"},
        headers=headers,
    )
    assert resp_inact_cat.status_code == 400
    assert "inactive" in resp_inact_cat.json()["detail"].lower()


def test_create_discount_rule_conflict_rejected(
    client: TestClient,
    admin_user: User,
    active_tier: CustomerTier,
    active_category: ProductCategory,
):
    """Verify duplicate active rules with identical tier, category, and priority are rejected with 400."""
    headers = _create_auth_headers(admin_user)
    payload = {
        "customer_tier_id": str(active_tier.id),
        "category_id": str(active_category.id),
        "max_discount_percent": "20.00",
        "priority": 5,
        "is_active": True,
    }
    resp1 = client.post("/api/v1/discount-rules", json=payload, headers=headers)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/discount-rules", json=payload, headers=headers)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"].lower()


# =====================================================================
# 2. LIST ENDPOINT TESTS (GET /api/v1/discount-rules)
# =====================================================================


def test_list_discount_rules_and_filtering(
    client: TestClient,
    admin_user: User,
    test_user: User,
    active_tier: CustomerTier,
    active_category: ProductCategory,
    db: Session,
):
    """Verify listing and filtering by customer tier, category, and active status."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    # 1. Create another tier & category for discrimination
    tier2 = CustomerTier(
        name=f"Tier2-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("10.00"),
        is_active=True,
    )
    cat2 = ProductCategory(
        name=f"Cat2-{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db.add_all([tier2, cat2])
    db.commit()

    # 2. Create 3 distinct rules
    r1 = client.post(
        "/api/v1/discount-rules",
        json={"customer_tier_id": str(active_tier.id), "max_discount_percent": "10.00", "priority": 1},
        headers=admin_h,
    ).json()

    r2 = client.post(
        "/api/v1/discount-rules",
        json={"category_id": str(active_category.id), "max_discount_percent": "20.00", "priority": 2},
        headers=admin_h,
    ).json()

    r3 = client.post(
        "/api/v1/discount-rules",
        json={
            "customer_tier_id": str(tier2.id),
            "category_id": str(cat2.id),
            "max_discount_percent": "30.00",
            "priority": 3,
            "is_active": False,
        },
        headers=admin_h,
    ).json()

    # Non-admin staff can read
    list_all = client.get("/api/v1/discount-rules", headers=rep_h)
    assert list_all.status_code == 200
    all_ids = {r["id"] for r in list_all.json()}
    assert r1["id"] in all_ids
    assert r2["id"] in all_ids
    assert r3["id"] in all_ids

    # Filter by customer tier
    filter_tier = client.get(
        f"/api/v1/discount-rules?customer_tier_id={active_tier.id}", headers=rep_h
    )
    assert filter_tier.status_code == 200
    assert any(r["id"] == r1["id"] for r in filter_tier.json())
    assert not any(r["id"] == r3["id"] for r in filter_tier.json())

    # Filter by category
    filter_cat = client.get(
        f"/api/v1/discount-rules?category_id={active_category.id}", headers=rep_h
    )
    assert filter_cat.status_code == 200
    assert any(r["id"] == r2["id"] for r in filter_cat.json())
    assert not any(r["id"] == r1["id"] for r in filter_cat.json())

    # Filter by active status
    filter_active = client.get("/api/v1/discount-rules?is_active=true", headers=rep_h)
    assert filter_active.status_code == 200
    assert not any(r["id"] == r3["id"] for r in filter_active.json())

    filter_inactive = client.get("/api/v1/discount-rules?is_active=false", headers=rep_h)
    assert filter_inactive.status_code == 200
    assert any(r["id"] == r3["id"] for r in filter_inactive.json())

    # Combined filters
    combined = client.get(
        f"/api/v1/discount-rules?customer_tier_id={tier2.id}&category_id={cat2.id}&is_active=false",
        headers=rep_h,
    )
    assert combined.status_code == 200
    assert len(combined.json()) == 1
    assert combined.json()[0]["id"] == r3["id"]


# =====================================================================
# 3. GET BY ID ENDPOINT TESTS (GET /api/v1/discount-rules/{id})
# =====================================================================


def test_get_discount_rule_by_id(
    client: TestClient, admin_user: User, test_user: User, active_tier: CustomerTier
):
    """Verify getting a discount rule by ID, including 404 for nonexistent rules."""
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    create_resp = client.post(
        "/api/v1/discount-rules",
        json={"customer_tier_id": str(active_tier.id), "max_discount_percent": "18.00"},
        headers=admin_h,
    )
    rule_id = create_resp.json()["id"]

    # Success
    get_resp = client.get(f"/api/v1/discount-rules/{rule_id}", headers=rep_h)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == rule_id
    assert Decimal(str(get_resp.json()["max_discount_percent"])) == Decimal("18.00")

    # Not found -> 404
    fake_id = str(uuid.uuid4())
    not_found_resp = client.get(f"/api/v1/discount-rules/{fake_id}", headers=rep_h)
    assert not_found_resp.status_code == 404


# =====================================================================
# 4. UPDATE ENDPOINT TESTS (PATCH /api/v1/discount-rules/{id})
# =====================================================================


def test_update_discount_rule_partial_and_validation(
    client: TestClient,
    admin_user: User,
    active_tier: CustomerTier,
    active_category: ProductCategory,
    db: Session,
):
    """Verify partial updates, reference updates, and conflict checks during update."""
    admin_h = _create_auth_headers(admin_user)

    # 1. Create base rule
    create_resp = client.post(
        "/api/v1/discount-rules",
        json={
            "customer_tier_id": str(active_tier.id),
            "max_discount_percent": "20.00",
            "priority": 5,
        },
        headers=admin_h,
    )
    rule_id = create_resp.json()["id"]

    # 2. Update max_discount_percent only
    patch_resp = client.patch(
        f"/api/v1/discount-rules/{rule_id}",
        json={"max_discount_percent": "28.50"},
        headers=admin_h,
    )
    assert patch_resp.status_code == 200
    assert Decimal(str(patch_resp.json()["max_discount_percent"])) == Decimal("28.50")
    assert patch_resp.json()["priority"] == 5
    assert patch_resp.json()["customer_tier_id"] == str(active_tier.id)

    # 3. Add category_id condition to rule
    patch_cat = client.patch(
        f"/api/v1/discount-rules/{rule_id}",
        json={"category_id": str(active_category.id)},
        headers=admin_h,
    )
    assert patch_cat.status_code == 200
    assert patch_cat.json()["category_id"] == str(active_category.id)

    # 4. Update with invalid percentage -> 422
    patch_inv = client.patch(
        f"/api/v1/discount-rules/{rule_id}",
        json={"max_discount_percent": "120.00"},
        headers=admin_h,
    )
    assert patch_inv.status_code == 422

    # 5. Update nonexistent rule -> 404
    fake_id = str(uuid.uuid4())
    patch_404 = client.patch(
        f"/api/v1/discount-rules/{fake_id}",
        json={"priority": 10},
        headers=admin_h,
    )
    assert patch_404.status_code == 404


# =====================================================================
# 5. DEACTIVATE ENDPOINT TESTS (DELETE /api/v1/discount-rules/{id})
# =====================================================================


def test_deactivate_discount_rule_logical_deactivation(
    client: TestClient, admin_user: User, active_tier: CustomerTier, db: Session
):
    """Verify DELETE logically deactivates the discount rule and preserves the database row."""
    admin_h = _create_auth_headers(admin_user)

    create_resp = client.post(
        "/api/v1/discount-rules",
        json={"customer_tier_id": str(active_tier.id), "max_discount_percent": "15.00"},
        headers=admin_h,
    )
    rule_id = create_resp.json()["id"]

    # Deactivate
    del_resp = client.delete(f"/api/v1/discount-rules/{rule_id}", headers=admin_h)
    assert del_resp.status_code == 200
    assert del_resp.json()["id"] == rule_id
    assert del_resp.json()["is_active"] is False

    # Confirm row is still present in database
    db_rule = db.get(DiscountRule, uuid.UUID(rule_id))
    assert db_rule is not None
    assert db_rule.is_active is False

    # Idempotent re-deactivation
    del_resp2 = client.delete(f"/api/v1/discount-rules/{rule_id}", headers=admin_h)
    assert del_resp2.status_code == 200
    assert del_resp2.json()["is_active"] is False

    # Nonexistent rule -> 404
    fake_id = str(uuid.uuid4())
    del_404 = client.delete(f"/api/v1/discount-rules/{fake_id}", headers=admin_h)
    assert del_404.status_code == 404


# =====================================================================
# 6. AUTHORIZATION (RBAC) TESTS
# =====================================================================


def test_discount_rules_role_authorization_matrix(
    client: TestClient,
    admin_user: User,
    test_user: User,
    sales_manager_user: User,
    finance_user: User,
    customer_user: User,
    active_tier: CustomerTier,
):
    """
    Verify complete RBAC matrix:
    - Admin: Full access (create, read, update, delete).
    - Internal staff (Sales Rep, Sales Manager, Finance Ops): Read allowed, mutations forbidden (403).
    - External customer: Forbidden on all discount endpoints (403).
    - Unauthenticated: Unauthorized on all endpoints (401).
    """
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)
    mgr_h = _create_auth_headers(sales_manager_user)
    fin_h = _create_auth_headers(finance_user)
    cust_h = _create_auth_headers(customer_user)

    # 1. Admin creates rule
    create_resp = client.post(
        "/api/v1/discount-rules",
        json={"customer_tier_id": str(active_tier.id), "max_discount_percent": "22.00"},
        headers=admin_h,
    )
    assert create_resp.status_code == 201
    rule_id = create_resp.json()["id"]

    # 2. Staff read permissions (all should succeed with 200)
    for staff_h in [rep_h, mgr_h, fin_h]:
        assert client.get("/api/v1/discount-rules", headers=staff_h).status_code == 200
        assert client.get(f"/api/v1/discount-rules/{rule_id}", headers=staff_h).status_code == 200

    # 3. Staff mutation attempts (all must fail with 403)
    for staff_h in [rep_h, mgr_h, fin_h]:
        assert client.post(
            "/api/v1/discount-rules",
            json={"customer_tier_id": str(active_tier.id), "max_discount_percent": "10.00"},
            headers=staff_h,
        ).status_code == 403

        assert client.patch(
            f"/api/v1/discount-rules/{rule_id}",
            json={"max_discount_percent": "25.00"},
            headers=staff_h,
        ).status_code == 403

        assert client.delete(
            f"/api/v1/discount-rules/{rule_id}",
            headers=staff_h,
        ).status_code == 403

    # 4. External customer user (all must fail with 403)
    assert client.get("/api/v1/discount-rules", headers=cust_h).status_code == 403
    assert client.get(f"/api/v1/discount-rules/{rule_id}", headers=cust_h).status_code == 403
    assert client.post("/api/v1/discount-rules", json={}, headers=cust_h).status_code == 403
    assert client.patch(f"/api/v1/discount-rules/{rule_id}", json={}, headers=cust_h).status_code == 403
    assert client.delete(f"/api/v1/discount-rules/{rule_id}", headers=cust_h).status_code == 403

    # 5. Unauthenticated user (all must fail with 401)
    assert client.get("/api/v1/discount-rules").status_code == 401
    assert client.get(f"/api/v1/discount-rules/{rule_id}").status_code == 401
    assert client.post("/api/v1/discount-rules", json={}).status_code == 401
    assert client.patch(f"/api/v1/discount-rules/{rule_id}", json={}).status_code == 401
    assert client.delete(f"/api/v1/discount-rules/{rule_id}").status_code == 401
