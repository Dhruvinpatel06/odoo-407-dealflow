"""Security utilities for DealFlow360 manual authentication."""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi.security import HTTPBearer

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

# HTTP Bearer scheme used for OpenAPI docs and token extraction
security_scheme = HTTPBearer(auto_error=False)

# Argon2id password hasher with default secure parameters
_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id password hash."""
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_access_token(
    user_id: Union[str, uuid.UUID],
    role: str,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a short-lived signed JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": str(role),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if "sub" not in payload:
            raise UnauthorizedError("Token missing required subject claim")
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Authentication token has expired")
    except jwt.InvalidTokenError as err:
        raise UnauthorizedError(f"Invalid authentication token: {str(err)}")


def generate_refresh_token() -> str:
    """Generate a high-entropy opaque refresh token."""
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """Hash an opaque refresh token using SHA-256 for persistent auth_sessions storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
