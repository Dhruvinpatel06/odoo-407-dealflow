from typing import Any, Callable, Dict, List, Optional
from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import security_scheme, verify_supabase_jwt

# Re-export get_db for convenient dependency access across modules
__all__ = ["get_db", "get_current_user", "require_roles"]


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
) -> Dict[str, Any]:
    """
    Dependency that extracts the Bearer token and resolves the authenticated Supabase user.
    """
    if not credentials:
        raise UnauthorizedError("Authorization header missing")
    return verify_supabase_jwt(credentials.credentials)


def require_roles(allowed_roles: List[str]) -> Callable[..., Dict[str, Any]]:
    """
    Dependency factory that checks role permissions against the authenticated user.
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise ForbiddenError("Insufficient permissions for this resource")
        return current_user

    return role_checker
