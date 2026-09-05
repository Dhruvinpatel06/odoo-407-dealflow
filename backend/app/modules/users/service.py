"""Users service layer."""

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.exceptions import DealFlowException, ResourceNotFoundError
from app.core.security import hash_password
from app.models.user import User
from app.modules.auth.repository import auth_repository
from app.modules.users.repository import user_repository
from app.modules.users.schemas import UserCreateRequest


class UserService:
    """Coordinates business logic and workflows for user management."""

    def create_user(self, db: Session, request: UserCreateRequest) -> User:
        """
        Create a new user with administrative authorization.
        Enforces unique email, hashes password with Argon2id, and persists user.
        """
        cleaned_email = request.email.strip().lower()
        existing = user_repository.get_by_email(db, cleaned_email)
        if existing:
            raise DealFlowException("A user with this email already exists", status_code=400)

        password_hash = hash_password(request.password)
        return user_repository.create_user(
            db=db,
            name=request.name,
            email=cleaned_email,
            password_hash=password_hash,
            role=request.role,
            customer_id=request.customer_id,
            is_active=request.is_active,
        )

    def get_user_by_id(self, db: Session, user_id: uuid.UUID) -> Optional[User]:
        """Fetch user by id."""
        return user_repository.get_by_id(db, user_id)

    def list_users(
        self,
        db: Session,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """List users with optional filtering."""
        return user_repository.list_users(
            db=db, role=role, is_active=is_active, skip=skip, limit=limit
        )

    def change_user_password(
        self, db: Session, user_id: uuid.UUID, new_password: str
    ) -> User:
        """
        Administratively change a target user's password.
        Rejects if user does not exist, updates password_hash with Argon2id,
        and revokes all active auth_sessions for the target user.
        """
        user = user_repository.get_by_id(db, user_id)
        if not user:
            raise ResourceNotFoundError(f"User with id '{user_id}' not found")

        new_hash = hash_password(new_password)
        updated_user = user_repository.update_password(db, user, new_hash)
        auth_repository.revoke_all_user_sessions(db, user.id)
        return updated_user


user_service = UserService()

