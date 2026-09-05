"""Users endpoints router for administrative user operations."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.modules.auth.schemas import UserResponse
from app.modules.users.schemas import UserCreateRequest
from app.modules.users.service import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List All Users (Admin Only)",
)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
) -> List[UserResponse]:
    """Retrieve all users in the system. Requires platform administrator permissions."""
    users = user_service.list_users(db)
    return [UserResponse.model_validate(u) for u in users]


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User (Admin Only)",
)
def create_user(
    request: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
) -> UserResponse:
    """Create a new user with specified role. Requires platform administrator permissions."""
    user = user_service.create_user(db, request)
    return UserResponse.model_validate(user)
