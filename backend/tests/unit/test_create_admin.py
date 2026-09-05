"""Unit tests for create_admin script logic."""

import pytest
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import verify_password
from scripts.create_admin import create_admin_user


def test_create_admin_user_success(db: Session):
    """Verify create_admin_user creates an active ADMIN user with Argon2id hash."""
    name = "Administrator User"
    email = "admin.seed@dealflow360.local"
    password = "SecureAdminPass123!"

    user = create_admin_user(
        db=db,
        name=name,
        email=email,
        password=password,
    )

    assert user.id is not None
    assert user.name == name
    assert user.email == email
    assert user.role == UserRole.ADMIN
    assert user.is_active is True
    assert user.customer_id is None

    # Verify password was hashed with Argon2id and plain is not stored
    assert user.password_hash.startswith("$argon2id$")
    assert user.password_hash != password
    assert verify_password(password, user.password_hash) is True


def test_create_admin_duplicate_email_fails_safely(db: Session):
    """Verify creating an admin with an existing email fails safely."""
    name = "Duplicate Admin"
    email = "existing.admin@dealflow360.local"
    password = "InitialPassword123!"

    # Create initial admin
    create_admin_user(db=db, name=name, email=email, password=password)

    # Attempt to create duplicate admin with same email (case-insensitive)
    with pytest.raises(ValueError) as exc_info:
        create_admin_user(
            db=db,
            name="Another Name",
            email=email.upper(),
            password="AnotherPassword123!",
        )

    assert "already exists" in str(exc_info.value).lower()


def test_create_admin_invalid_inputs(db: Session):
    """Verify validation for empty name, invalid email, or short password."""
    # Empty name
    with pytest.raises(ValueError, match="Name cannot be empty"):
        create_admin_user(db=db, name="  ", email="valid@dealflow360.local", password="Password123!")

    # Invalid email
    with pytest.raises(ValueError, match="valid email"):
        create_admin_user(db=db, name="Admin", email="invalid-email", password="Password123!")

    # Short password (< 8 chars)
    with pytest.raises(ValueError, match="at least 8 characters"):
        create_admin_user(db=db, name="Admin", email="valid@dealflow360.local", password="short")
