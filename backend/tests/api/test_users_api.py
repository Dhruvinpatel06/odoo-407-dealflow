"""Tests for public customer signup and administrative user creation endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import create_access_token, verify_password
from app.models.user import User


def test_successful_customer_signup(client: TestClient, db: Session):
    """Verify customer signup creates active CUSTOMER user with Argon2id hash and no session."""
    payload = {
        "name": "Jane Customer",
        "email": "jane.customer@example.com",
        "password": "CustomerSecure123!",
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()

    # Verify response fields
    assert "id" in data
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"].lower()
    assert data["role"] == UserRole.CUSTOMER.value
    assert data["is_active"] is True
    assert data["customer_id"] is None
    assert "password_hash" not in data
    assert "password" not in data

    # Verify no auth session or refresh cookie created
    assert "refresh_token" not in response.cookies

    # Verify database persistence & Argon2id password hash
    stmt = select(User).where(User.email == payload["email"].lower())
    user = db.scalars(stmt).first()
    assert user is not None
    assert user.role == UserRole.CUSTOMER
    assert user.is_active is True
    assert user.password_hash.startswith("$argon2id$")
    assert user.password_hash != payload["password"]
    assert verify_password(payload["password"], user.password_hash) is True


def test_signup_always_creates_customer_and_cannot_override_role(
    client: TestClient, db: Session
):
    """Verify client-supplied role is ignored and newly created user always receives CUSTOMER."""
    payload = {
        "name": "Attacker Role Attempt",
        "email": "attacker.role@example.com",
        "password": "Password123!",
        "role": "ADMIN",  # Attempt to inject privileged role
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == UserRole.CUSTOMER.value

    # Verify database record is CUSTOMER, never ADMIN
    stmt = select(User).where(User.email == payload["email"].lower())
    user = db.scalars(stmt).first()
    assert user.role == UserRole.CUSTOMER


def test_signup_duplicate_email_rejection(client: TestClient, test_user: User):
    """Verify signup rejects already registered emails."""
    payload = {
        "name": "Duplicate User",
        "email": test_user.email.upper(),  # Test case-insensitivity
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_admin_user_creation_success(
    client: TestClient, admin_user: User, db: Session
):
    """Verify admin can create a user and password is stored as Argon2id hash."""
    admin_token = create_access_token(user_id=admin_user.id, role=admin_user.role.value)
    payload = {
        "name": "New Sales Rep",
        "email": "new.rep@dealflow360.local",
        "password": "SalesRepPass123!",
        "role": UserRole.SALES_REP.value,
        "is_active": True,
    }

    response = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=payload,
    )
    assert response.status_code == 201
    data = response.json()

    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert data["role"] == UserRole.SALES_REP.value
    assert data["is_active"] is True
    assert "password" not in data
    assert "password_hash" not in data

    # Verify database record and password hashing
    stmt = select(User).where(User.email == payload["email"])
    user = db.scalars(stmt).first()
    assert user is not None
    assert user.role == UserRole.SALES_REP
    assert user.password_hash.startswith("$argon2id$")
    assert verify_password(payload["password"], user.password_hash) is True


def test_admin_can_select_each_supported_role(client: TestClient, admin_user: User, db: Session):
    """Verify admin can create users for all five supported application roles."""
    admin_token = create_access_token(user_id=admin_user.id, role=admin_user.role.value)
    supported_roles = [
        UserRole.CUSTOMER,
        UserRole.SALES_REP,
        UserRole.SALES_MANAGER,
        UserRole.FINANCE_OPERATIONS,
        UserRole.ADMIN,
    ]

    for role in supported_roles:
        email = f"user.{role.value.lower()}@dealflow360.local"
        payload = {
            "name": f"User {role.value}",
            "email": email,
            "password": "SecurePassword123!",
            "role": role.value,
            "is_active": True,
        }
        response = client.post(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=payload,
        )
        assert response.status_code == 201, f"Failed for role {role.value}: {response.text}"
        data = response.json()
        assert data["role"] == role.value

        stmt = select(User).where(User.email == email)
        persisted = db.scalars(stmt).first()
        assert persisted.role == role


def test_non_admin_cannot_create_users(
    client: TestClient, test_user: User
):
    """Verify non-admin roles and unauthenticated requests are forbidden from creating users."""
    payload = {
        "name": "Unauthorized Attempt",
        "email": "unauthorized@dealflow360.local",
        "password": "Password123!",
        "role": UserRole.CUSTOMER.value,
    }

    # 1. Non-admin (SALES_REP) receives 403 Forbidden
    rep_token = create_access_token(user_id=test_user.id, role=test_user.role.value)
    forbidden_resp = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {rep_token}"},
        json=payload,
    )
    assert forbidden_resp.status_code == 403

    # 2. Unauthenticated request receives 401 Unauthorized
    unauth_resp = client.post(
        "/api/v1/users",
        json=payload,
    )
    assert unauth_resp.status_code == 401


def test_admin_user_creation_duplicate_email_rejection(
    client: TestClient, admin_user: User, test_user: User
):
    """Verify admin user creation rejects duplicate email addresses."""
    admin_token = create_access_token(user_id=admin_user.id, role=admin_user.role.value)
    payload = {
        "name": "Duplicate User",
        "email": test_user.email,
        "password": "Password123!",
        "role": UserRole.SALES_REP.value,
    }
    response = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=payload,
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()
