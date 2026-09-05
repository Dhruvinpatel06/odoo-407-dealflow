import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.modules.auth.schemas import MessageResponse
from app.modules.users.schemas import (
    AdminChangePasswordRequest,
    UserCreateRequest,
    UserResponse,
)
from app.modules.users.service import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User (Admin Only)",
)
def create_user(
    request: UserCreateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Create a new application user from the administrative interface.
    Requires ADMIN authorization. Supports all application roles.
    """
    user = user_service.create_user(db=db, request=request)
    return UserResponse.model_validate(user)


@router.get(
    "",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List Users",
)
def list_users(
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.SALES_MANAGER])
    ),
    db: Session = Depends(get_db),
) -> List[UserResponse]:
    """
    List application users. Accessible to ADMIN and SALES_MANAGER.
    """
    users = user_service.list_users(
        db=db, role=role, is_active=is_active, skip=skip, limit=limit
    )
    return [UserResponse.model_validate(u) for u in users]


@router.post(
    "/{user_id}/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change User Password (Admin Only)",
)
def admin_change_password(
    user_id: uuid.UUID,
    request: AdminChangePasswordRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Administratively change the password of any user.
    Requires ADMIN authorization. Revokes all active sessions of the target user.
    """
    user_service.change_user_password(
        db=db, user_id=user_id, new_password=request.new_password
    )
    return MessageResponse(message="Password changed successfully")
