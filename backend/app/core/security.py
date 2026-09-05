from typing import Any, Dict
from fastapi.security import HTTPBearer
from app.core.exceptions import UnauthorizedError

# HTTP Bearer scheme used for OpenAPI docs and token extraction
security_scheme = HTTPBearer(auto_error=False)


def verify_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Placeholder structure for Supabase JWT verification.
    Full verification will decode and validate the token against SUPABASE_JWT_SECRET
    in the upcoming authentication task.
    """
    if not token:
        raise UnauthorizedError("Missing authentication token")

    # Basic structural dictionary returned for downstream authorization wiring
    return {
        "sub": "placeholder-user-id",
        "role": "authenticated",
        "email": "user@dealflow360.local",
    }
