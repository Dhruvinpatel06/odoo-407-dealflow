"""Tests for Customer Tier CRUD endpoints."""

import uuid
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import create_access_token
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.user import User


def _create_auth_headers(user: User) -> dict:
    """Helper to generate Authorization header for a given user."""
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


def test_create_customer_tier_success(client: TestClient, admin_user: User):
    """Verify ADMIN can create a valid customer tier."""
    headers = _create_auth_headers(admin_user)
    payload = {
        "name": "Platinum Tier",
        "description": "Enterprise VIP customers",
        "default_discount_limit": "25.00",
        "is_active": True,
    }
    response = client.post("/api/v1/customer-tiers", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Platinum Tier"
    assert data["description"] == "Enterprise VIP customers"
    assert Decimal(str(data["default_discount_limit"])) == Decimal("25.00")
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_customer_tier_duplicate_name_fails(client: TestClient, admin_user: User):
    """Verify creating a tier with an existing name returns 400."""
    headers = _create_auth_headers(admin_user)
    payload = {
        "name": "Gold Tier",
        "default_discount_limit": "15.00",
    }
    resp1 = client.post("/api/v1/customer-tiers", json=payload, headers=headers)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/customer-tiers", json=payload, headers=headers)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"].lower()


def test_create_customer_tier_permissions(
    client: TestClient, test_user: User, admin_user: User
):
    """Verify SALES_REP cannot create a customer tier (403), but SALES_MANAGER can (201)."""
    # SALES_REP should be forbidden
    rep_headers = _create_auth_headers(test_user)
    payload = {"name": "Silver Tier", "default_discount_limit": "10.00"}
    resp_rep = client.post("/api/v1/customer-tiers", json=payload, headers=rep_headers)
    assert resp_rep.status_code == 403

    # Unauthenticated should be 401
    resp_unauth = client.post("/api/v1/customer-tiers", json=payload)
    assert resp_unauth.status_code == 401


def test_create_customer_tier_invalid_discount_limit(client: TestClient, admin_user: User):
    """Verify discount limit outside 0-100 fails with 422."""
    headers = _create_auth_headers(admin_user)
    payload = {"name": "Invalid Tier", "default_discount_limit": "150.00"}
    resp = client.post("/api/v1/customer-tiers", json=payload, headers=headers)
    assert resp.status_code == 422


def test_list_customer_tiers(client: TestClient, admin_user: User, test_user: User):
    """Verify listing customer tiers with optional active filter."""
    admin_headers = _create_auth_headers(admin_user)
    rep_headers = _create_auth_headers(test_user)

    # Create active and inactive tiers
    client.post(
        "/api/v1/customer-tiers",
        json={"name": "Tier Active 1", "default_discount_limit": "5.00", "is_active": True},
        headers=admin_headers,
    )
    client.post(
        "/api/v1/customer-tiers",
        json={"name": "Tier Inactive 1", "default_discount_limit": "5.00", "is_active": False},
        headers=admin_headers,
    )

    # SALES_REP can list tiers
    resp = client.get("/api/v1/customer-tiers", headers=rep_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2

    # Filter active
    resp_active = client.get("/api/v1/customer-tiers?is_active=true", headers=rep_headers)
    assert resp_active.status_code == 200
    for item in resp_active.json():
        assert item["is_active"] is True

    # Filter inactive
    resp_inactive = client.get("/api/v1/customer-tiers?is_active=false", headers=rep_headers)
    assert resp_inactive.status_code == 200
    for item in resp_inactive.json():
        assert item["is_active"] is False


def test_get_customer_tier_by_id(client: TestClient, admin_user: User, test_user: User):
    """Verify retrieving a customer tier by ID."""
    admin_headers = _create_auth_headers(admin_user)
    rep_headers = _create_auth_headers(test_user)

    create_resp = client.post(
        "/api/v1/customer-tiers",
        json={"name": "Bronze Tier", "default_discount_limit": "5.00"},
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    tier_id = create_resp.json()["id"]

    # Retrieve by ID
    get_resp = client.get(f"/api/v1/customer-tiers/{tier_id}", headers=rep_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == tier_id
    assert get_resp.json()["name"] == "Bronze Tier"

    # Non-existent ID -> 404
    non_existent = str(uuid.uuid4())
    get_404 = client.get(f"/api/v1/customer-tiers/{non_existent}", headers=rep_headers)
    assert get_404.status_code == 404


def test_update_customer_tier(client: TestClient, admin_user: User):
    """Verify PATCH /api/v1/customer-tiers/{id} updates tier fields."""
    headers = _create_auth_headers(admin_user)

    create_resp = client.post(
        "/api/v1/customer-tiers",
        json={"name": "Updatable Tier", "default_discount_limit": "8.00"},
        headers=headers,
    )
    assert create_resp.status_code == 201
    tier_id = create_resp.json()["id"]

    # Patch updates
    patch_resp = client.patch(
        f"/api/v1/customer-tiers/{tier_id}",
        json={"name": "Renamed Tier", "default_discount_limit": "12.50", "description": "Updated desc"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    updated_data = patch_resp.json()
    assert updated_data["name"] == "Renamed Tier"
    assert Decimal(str(updated_data["default_discount_limit"])) == Decimal("12.50")
    assert updated_data["description"] == "Updated desc"


def test_update_customer_tier_duplicate_name_conflict(client: TestClient, admin_user: User):
    """Verify renaming a tier to an existing name fails with 400."""
    headers = _create_auth_headers(admin_user)

    client.post(
        "/api/v1/customer-tiers",
        json={"name": "Existing Tier A", "default_discount_limit": "10.00"},
        headers=headers,
    )
    t2 = client.post(
        "/api/v1/customer-tiers",
        json={"name": "Existing Tier B", "default_discount_limit": "10.00"},
        headers=headers,
    ).json()

    patch_resp = client.patch(
        f"/api/v1/customer-tiers/{t2['id']}",
        json={"name": "Existing Tier A"},
        headers=headers,
    )
    assert patch_resp.status_code == 400


def test_delete_customer_tier_logical_deactivation(
    client: TestClient, admin_user: User, db: Session
):
    """Verify DELETE /api/v1/customer-tiers/{id} performs logical deactivation."""
    headers = _create_auth_headers(admin_user)

    create_resp = client.post(
        "/api/v1/customer-tiers",
        json={"name": "Tier To Deactivate", "default_discount_limit": "7.00", "is_active": True},
        headers=headers,
    )
    tier_id = create_resp.json()["id"]

    # Call DELETE
    del_resp = client.delete(f"/api/v1/customer-tiers/{tier_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["is_active"] is False

    # Verify tier row still exists in database and is_active is False
    tier_in_db = db.get(CustomerTier, uuid.UUID(tier_id))
    assert tier_in_db is not None
    assert tier_in_db.is_active is False


def test_delete_referenced_customer_tier_does_not_physically_delete(
    client: TestClient, admin_user: User, db: Session
):
    """
    Verify that a customer tier referenced by an existing customer is not
    physically deleted and is safely logically deactivated.
    """
    headers = _create_auth_headers(admin_user)

    create_resp = client.post(
        "/api/v1/customer-tiers",
        json={"name": "Referenced Tier", "default_discount_limit": "15.00"},
        headers=headers,
    )
    tier_id = uuid.UUID(create_resp.json()["id"])

    # Create a customer referencing this tier
    customer = Customer(
        name="Acme Corp",
        email="contact@acme.com",
        customer_tier_id=tier_id,
        is_active=True,
    )
    db.add(customer)
    db.commit()

    # Call DELETE endpoint
    del_resp = client.delete(f"/api/v1/customer-tiers/{tier_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["is_active"] is False

    # Verify tier still exists in DB and is deactivated
    tier_in_db = db.get(CustomerTier, tier_id)
    assert tier_in_db is not None
    assert tier_in_db.is_active is False
    assert tier_in_db.id == customer.customer_tier_id


def test_customer_tier_endpoints_role_based_matrix(client: TestClient, admin_user: User, db: Session):
    """
    Step 11 Authorization Test:
    Verify role-based authorization matrix for all Customer Tier endpoints.
    - CUSTOMER: 403 on all operations (GET list, GET id, POST, PATCH, DELETE).
    - SALES_REP & FINANCE_OPERATIONS: 200 on GET list and GET id; 403 on POST, PATCH, DELETE.
    - SALES_MANAGER & ADMIN: 200/201 on all operations (GET, POST, PATCH, DELETE).
    """
    # Create tier for testing read/update/delete
    admin_h = _create_auth_headers(admin_user)
    tier_resp = client.post(
        "/api/v1/customer-tiers",
        json={"name": f"Tier Matrix {uuid.uuid4().hex[:4]}", "default_discount_limit": "10.00"},
        headers=admin_h,
    )
    assert tier_resp.status_code == 201
    tier_id = tier_resp.json()["id"]

    manager_user = User(
        name="Tier Mgr",
        email=f"tmgr-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.SALES_MANAGER,
        is_active=True,
    )
    rep_user = User(
        name="Tier Rep",
        email=f"trep-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.SALES_REP,
        is_active=True,
    )
    finance_user = User(
        name="Tier Finance",
        email=f"tfin-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.FINANCE_OPERATIONS,
        is_active=True,
    )
    cust_user = User(
        name="Tier Customer",
        email=f"tcust-{uuid.uuid4().hex[:6]}@test.local",
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

    create_payload = {"name": f"New Tier {uuid.uuid4().hex[:4]}", "default_discount_limit": "5.00"}

    # 1. CUSTOMER: Blocked from all tier endpoints (403)
    assert client.get("/api/v1/customer-tiers", headers=cust_h).status_code == 403
    assert client.get(f"/api/v1/customer-tiers/{tier_id}", headers=cust_h).status_code == 403
    assert client.post("/api/v1/customer-tiers", json=create_payload, headers=cust_h).status_code == 403
    assert client.patch(f"/api/v1/customer-tiers/{tier_id}", json={"name": "Cust Tier Try"}, headers=cust_h).status_code == 403
    assert client.delete(f"/api/v1/customer-tiers/{tier_id}", headers=cust_h).status_code == 403

    # 2. SALES_REP: Allowed on read (GET list, GET id); Forbidden on write (POST, PATCH, DELETE)
    assert client.get("/api/v1/customer-tiers", headers=rep_h).status_code == 200
    assert client.get(f"/api/v1/customer-tiers/{tier_id}", headers=rep_h).status_code == 200
    assert client.post("/api/v1/customer-tiers", json=create_payload, headers=rep_h).status_code == 403
    assert client.patch(f"/api/v1/customer-tiers/{tier_id}", json={"name": "Rep Tier Try"}, headers=rep_h).status_code == 403
    assert client.delete(f"/api/v1/customer-tiers/{tier_id}", headers=rep_h).status_code == 403

    # 3. FINANCE_OPERATIONS: Allowed on read (GET list, GET id); Forbidden on write (POST, PATCH, DELETE)
    assert client.get("/api/v1/customer-tiers", headers=finance_h).status_code == 200
    assert client.get(f"/api/v1/customer-tiers/{tier_id}", headers=finance_h).status_code == 200
    assert client.post("/api/v1/customer-tiers", json=create_payload, headers=finance_h).status_code == 403
    assert client.patch(f"/api/v1/customer-tiers/{tier_id}", json={"name": "Fin Tier Try"}, headers=finance_h).status_code == 403
    assert client.delete(f"/api/v1/customer-tiers/{tier_id}", headers=finance_h).status_code == 403

    # 4. SALES_MANAGER: Allowed on all (GET, POST, PATCH, DELETE)
    assert client.get("/api/v1/customer-tiers", headers=manager_h).status_code == 200
    assert client.get(f"/api/v1/customer-tiers/{tier_id}", headers=manager_h).status_code == 200
    mgr_create = client.post(
        "/api/v1/customer-tiers",
        json={"name": f"Mgr Tier {uuid.uuid4().hex[:4]}", "default_discount_limit": "8.00"},
        headers=manager_h,
    )
    assert mgr_create.status_code == 201
    mgr_tier_id = mgr_create.json()["id"]

    mgr_patch = client.patch(
        f"/api/v1/customer-tiers/{mgr_tier_id}",
        json={"name": f"Mgr Updated {uuid.uuid4().hex[:4]}"},
        headers=manager_h,
    )
    assert mgr_patch.status_code == 200

    mgr_del = client.delete(f"/api/v1/customer-tiers/{mgr_tier_id}", headers=manager_h)
    assert mgr_del.status_code == 200

    # 5. ADMIN: Allowed on all
    assert client.get("/api/v1/customer-tiers", headers=admin_h).status_code == 200
    assert client.get(f"/api/v1/customer-tiers/{tier_id}", headers=admin_h).status_code == 200
    assert client.patch(f"/api/v1/customer-tiers/{tier_id}", json={"default_discount_limit": "18.00"}, headers=admin_h).status_code == 200
    assert client.delete(f"/api/v1/customer-tiers/{tier_id}", headers=admin_h).status_code == 200
