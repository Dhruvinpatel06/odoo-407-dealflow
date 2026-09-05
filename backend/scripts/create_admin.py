"""One-time interactive seed script to create an initial ADMIN user for DealFlow360."""

import getpass
import os
import sys
from typing import Optional

# Ensure backend directory is on sys.path for direct script invocation
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User


def create_admin_user(
    db: Session,
    name: str,
    email: str,
    password: str,
) -> User:
    """
    Validate, hash credentials, and persist an ADMIN user.
    Fails safely if a user with the specified email already exists.
    """
    cleaned_name = name.strip()
    cleaned_email = email.strip().lower()

    if not cleaned_name:
        raise ValueError("Name cannot be empty.")

    if not cleaned_email or "@" not in cleaned_email:
        raise ValueError("A valid email address is required.")

    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    # Check for duplicate email (case-insensitive)
    existing_user = db.scalars(
        select(User).where(func.lower(User.email) == cleaned_email)
    ).first()
    if existing_user:
        raise ValueError(f"A user with email '{cleaned_email}' already exists.")

    # Hash the password using Argon2id via existing hash_password()
    password_hash = hash_password(password)

    admin_user = User(
        name=cleaned_name,
        email=cleaned_email,
        password_hash=password_hash,
        role=UserRole.ADMIN,
        is_active=True,
        customer_id=None,
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return admin_user


def main() -> None:
    """Prompt interactively for admin credentials and persist the user."""
    print("=" * 60)
    print("DealFlow360 — Create Initial Admin User")
    print("=" * 60)

    try:
        name = input("Enter admin full name: ").strip()
        if not name:
            print("Error: Name cannot be empty.", file=sys.stderr)
            sys.exit(1)

        email = input("Enter admin email: ").strip()
        if not email or "@" not in email:
            print("Error: Please provide a valid email address.", file=sys.stderr)
            sys.exit(1)

        password = getpass.getpass("Enter admin password (min 8 chars): ")
        if not password or len(password) < 8:
            print("Error: Password must be at least 8 characters long.", file=sys.stderr)
            sys.exit(1)

        confirm_password = getpass.getpass("Confirm admin password: ")
        if password != confirm_password:
            print("Error: Passwords do not match.", file=sys.stderr)
            sys.exit(1)

        with SessionLocal() as db:
            user = create_admin_user(
                db=db,
                name=name,
                email=email,
                password=password,
            )
            print("-" * 60)
            print(f"SUCCESS: Admin user created successfully!")
            print(f"  ID:     {user.id}")
            print(f"  Name:   {user.name}")
            print(f"  Email:  {user.email}")
            print(f"  Role:   {user.role.value}")
            print(f"  Active: {user.is_active}")
            print("-" * 60)

    except ValueError as val_err:
        print(f"Error: {val_err}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
