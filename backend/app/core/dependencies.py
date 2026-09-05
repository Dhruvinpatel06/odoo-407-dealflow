"""Authentication and authorization dependencies for DealFlow360."""

import uuid
from typing import Callable, List, Optional, Union

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token, security_scheme
from app.models.user import User

__all__ = ["get_db", "get_current_user", "require_roles"]


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate the Bearer access token, then resolve the authoritative
    user from PostgreSQL. Rejects nonexistent and inactive users.
    """
    if not credentials:
        raise UnauthorizedError("Authorization header missing")

    payload = decode_access_token(credentials.credentials)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError("Token missing subject identifier")

    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise UnauthorizedError("Invalid user identity in token")

    user = db.get(User, user_id)
    if not user:
        raise UnauthorizedError("User not found")

    if not user.is_active:
        raise UnauthorizedError("User account is inactive")

    return user


def require_roles(allowed_roles: List[Union[str, UserRole]]) -> Callable[..., User]:
    """
    Dependency factory that checks role permissions against the authoritative database user.
    """
    normalized_roles = {
        role.value if isinstance(role, UserRole) else str(role)
        for role in allowed_roles
    }

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_val = (
            current_user.role.value
            if isinstance(current_user.role, UserRole)
            else str(current_user.role)
        )
        if user_role_val not in normalized_roles:
            raise ForbiddenError("Insufficient permissions for this resource")
        return current_user

    return role_checker
