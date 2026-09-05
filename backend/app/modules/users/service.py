"""Service layer for user administration."""

from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import DealFlowException
from app.core.security import hash_password
from app.models.user import User
from app.modules.users.schemas import UserCreateRequest


class UserService:
    """Coordinates administrative user lifecycle operations."""

    def list_users(self, db: Session) -> List[User]:
        """Fetch all registered users ordered by registration date descending."""
        stmt = select(User).order_by(User.created_at.desc())
        return list(db.execute(stmt).scalars().all())

    def create_user(self, db: Session, request: UserCreateRequest) -> User:
        """Create a new user with administrative authorization."""
        email_clean = request.email.strip().lower()
        stmt = select(User).where(User.email == email_clean)
        existing = db.execute(stmt).scalar_one_or_none()
        if existing:
            raise DealFlowException("Email already registered", status_code=400)

        hashed_pwd = hash_password(request.password)
        new_user = User(
            name=request.name.strip(),
            email=email_clean,
            password_hash=hashed_pwd,
            role=request.role,
            customer_id=request.customer_id,
            is_active=request.is_active,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user


user_service = UserService()
