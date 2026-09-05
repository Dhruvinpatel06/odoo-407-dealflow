"""Unit tests for security primitives: Argon2id, JWT, and opaque refresh tokens."""

import uuid
from datetime import timedelta
import pytest

from app.common.enums import UserRole
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_argon2_password_hashing():
    """Verify Argon2id hashes passwords securely and verifies correctly."""
    plain = "SuperSecret123!"
    hashed = hash_password(plain)

    # Argon2id prefix check
    assert hashed.startswith("$argon2id$")
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_access_token_lifecycle():
    """Verify JWT access token creation and decoding."""
    user_id = uuid.uuid4()
    role = UserRole.SALES_MANAGER

    token = create_access_token(user_id=user_id, role=role.value)
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == role.value
    assert "exp" in payload
    assert "iat" in payload
    assert "jti" in payload


def test_jwt_access_token_tampered():
    """Verify tampered JWT tokens are rejected with UnauthorizedError."""
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, role="ADMIN")
    tampered_token = token[:-5] + "XXXXX"

    with pytest.raises(UnauthorizedError):
        decode_access_token(tampered_token)


def test_jwt_access_token_expired():
    """Verify expired JWT tokens are rejected."""
    user_id = uuid.uuid4()
    # Create token with -1 minute expiration
    expired_token = create_access_token(
        user_id=user_id,
        role="CUSTOMER",
        extra_claims={"exp": 1000},
    )

    with pytest.raises(UnauthorizedError) as exc_info:
        decode_access_token(expired_token)
    assert "expired" in str(exc_info.value.message).lower()


def test_opaque_refresh_token_generation_and_hashing():
    """Verify opaque refresh token generation entropy and SHA-256 hashing."""
    token1 = generate_refresh_token()
    token2 = generate_refresh_token()

    assert len(token1) >= 64
    assert len(token2) >= 64
    assert token1 != token2

    hash1 = hash_refresh_token(token1)
    hash2 = hash_refresh_token(token2)

    # SHA-256 output is 64 hex characters
    assert len(hash1) == 64
    assert len(hash2) == 64
    assert hash1 != hash2

    # Deterministic hashing of the same raw token
    assert hash_refresh_token(token1) == hash1
