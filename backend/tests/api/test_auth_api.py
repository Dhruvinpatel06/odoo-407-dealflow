"""API tests for DealFlow360 manual authentication endpoints."""

import uuid
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.config import settings
from app.core.dependencies import get_current_user, require_roles
from app.core.security import create_access_token
from app.main import app
from app.models.auth_session import AuthSession
from app.models.user import User

# Temporary test route to verify role-based authorization dependency
_test_router = APIRouter(prefix="/test-auth")


@_test_router.get("/admin-only")
def admin_only_endpoint(current_user: User = Depends(require_roles([UserRole.ADMIN]))):
    return {"status": "authorized", "user_id": str(current_user.id)}


app.include_router(_test_router)


def test_login_success(client: TestClient, test_user: User, db: Session):
    """Verify login authenticates credentials, returns JWT, sets cookie, and records session."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # Verify HttpOnly cookie attached
    assert settings.REFRESH_COOKIE_NAME in response.cookies
    refresh_token = response.cookies[settings.REFRESH_COOKIE_NAME]
    assert len(refresh_token) >= 64

    # Verify auth_sessions record in database
    stmt = select(AuthSession).where(AuthSession.user_id == test_user.id)
    session = db.scalars(stmt).first()
    assert session is not None
    assert session.revoked_at is None
    assert session.expires_at is not None


def test_login_invalid_password(client: TestClient, test_user: User):
    """Verify login rejects incorrect password."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_login_unknown_email(client: TestClient):
    """Verify login rejects non-existent email."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@dealflow360.local", "password": "Password123!"},
    )
    assert response.status_code == 401


def test_login_inactive_user(client: TestClient, inactive_user: User):
    """Verify login rejects inactive users."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": inactive_user.email, "password": "Password123!"},
    )
    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()


def test_refresh_token_rotation(client: TestClient, test_user: User, db: Session):
    """Verify refresh token rotation returns a new access token and replaces the refresh cookie."""
    # 1. Login to establish session
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    original_refresh_cookie = login_resp.cookies.get(settings.REFRESH_COOKIE_NAME)
    assert original_refresh_cookie is not None

    # 2. Call refresh endpoint with cookie
    client.cookies.set(settings.REFRESH_COOKIE_NAME, original_refresh_cookie)
    refresh_resp = client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 200
    refresh_data = refresh_resp.json()
    assert "access_token" in refresh_data

    # 3. Verify new refresh token cookie was issued
    new_refresh_cookie = refresh_resp.cookies.get(settings.REFRESH_COOKIE_NAME)
    assert new_refresh_cookie is not None
    assert new_refresh_cookie != original_refresh_cookie

    # 4. Old refresh token should now fail
    client.cookies.set(settings.REFRESH_COOKIE_NAME, original_refresh_cookie)
    failed_resp = client.post("/api/v1/auth/refresh")
    assert failed_resp.status_code == 401


def test_refresh_missing_cookie(client: TestClient):
    """Verify refresh endpoint rejects requests with missing cookie."""
    client.cookies.clear()
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


def test_refresh_revoked_session(client: TestClient, test_user: User, db: Session):
    """Verify refresh endpoint rejects revoked sessions."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    refresh_cookie = login_resp.cookies.get(settings.REFRESH_COOKIE_NAME)

    # Manually revoke the session in the database
    stmt = select(AuthSession).where(AuthSession.user_id == test_user.id)
    session = db.scalars(stmt).first()
    session.revoked_at = db.query(AuthSession).first().created_at
    db.commit()

    client.cookies.set(settings.REFRESH_COOKIE_NAME, refresh_cookie)
    resp = client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


def test_logout_revokes_session_and_clears_cookie(client: TestClient, test_user: User, db: Session):
    """Verify logout revokes the server session and clears client cookie."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    refresh_cookie = login_resp.cookies.get(settings.REFRESH_COOKIE_NAME)
    client.cookies.set(settings.REFRESH_COOKIE_NAME, refresh_cookie)

    logout_resp = client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "Logged out successfully"

    # Verify session revoked in database
    stmt = select(AuthSession).where(AuthSession.user_id == test_user.id)
    session = db.scalars(stmt).first()
    assert session.revoked_at is not None

    # Subsequent refresh should be rejected
    client.cookies.set(settings.REFRESH_COOKIE_NAME, refresh_cookie)
    fail_refresh = client.post("/api/v1/auth/refresh")
    assert fail_refresh.status_code == 401


def test_get_me_success(client: TestClient, test_user: User):
    """Verify /auth/me returns authenticated user data without exposing secrets."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    access_token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email
    assert data["role"] == test_user.role.value
    assert data["is_active"] is True
    assert "password_hash" not in data
    assert "refresh_token" not in data


def test_get_me_unauthorized(client: TestClient):
    """Verify /auth/me returns 401 without Bearer token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_change_password_flow(client: TestClient, test_user: User, db: Session):
    """Verify change-password updates hash, revokes sessions, and requires new credentials."""
    # 1. Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    access_token = login_resp.json()["access_token"]
    old_cookie = login_resp.cookies.get(settings.REFRESH_COOKIE_NAME)

    # 2. Reject incorrect current password
    fail_change = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current_password": "WrongPassword!", "new_password": "BrandNewPassword456!"},
    )
    assert fail_change.status_code == 401

    # 3. Successful change
    success_change = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current_password": "Password123!", "new_password": "BrandNewPassword456!"},
    )
    assert success_change.status_code == 200

    # 4. Old refresh token session is revoked
    client.cookies.set(settings.REFRESH_COOKIE_NAME, old_cookie)
    revoked_refresh = client.post("/api/v1/auth/refresh")
    assert revoked_refresh.status_code == 401

    # 5. Old password login rejected
    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    assert old_login.status_code == 401

    # 6. New password login succeeds
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "BrandNewPassword456!"},
    )
    assert new_login.status_code == 200


def test_role_authorization_and_authoritative_db_checks(
    client: TestClient, test_user: User, admin_user: User, db: Session
):
    """Verify require_roles enforces role hierarchy and database active state authoritatively."""
    # 1. SALES_REP accessing admin-only endpoint -> 403 Forbidden
    rep_token = create_access_token(user_id=test_user.id, role=test_user.role.value)
    forbidden_resp = client.get(
        "/test-auth/admin-only",
        headers={"Authorization": f"Bearer {rep_token}"},
    )
    assert forbidden_resp.status_code == 403

    # 2. ADMIN accessing admin-only endpoint -> 200 OK
    admin_token = create_access_token(user_id=admin_user.id, role=admin_user.role.value)
    allowed_resp = client.get(
        "/test-auth/admin-only",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert allowed_resp.status_code == 200

    # 3. Deactivated user in DB with a still-valid token -> 401 Unauthorized
    admin_user.is_active = False
    db.commit()

    deactivated_resp = client.get(
        "/test-auth/admin-only",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert deactivated_resp.status_code == 401
    assert "inactive" in deactivated_resp.json()["detail"].lower()
