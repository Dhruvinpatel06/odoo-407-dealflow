"""Users repository layer."""

import uuid
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.models.user import User


class UserRepository:
    """Encapsulates persistence operations for the User entity."""

    def get_by_id(self, db: Session, user_id: uuid.UUID) -> Optional[User]:
        """Fetch user by primary key."""
        return db.get(User, user_id)

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Fetch user by email (case-insensitive)."""
        stmt = select(User).where(func.lower(User.email) == email.strip().lower())
        return db.scalars(stmt).first()

    def create_user(
        self,
        db: Session,
        name: str,
        email: str,
        password_hash: str,
        role: UserRole,
        customer_id: Optional[uuid.UUID] = None,
        is_active: bool = True,
    ) -> User:
        """Create and persist a new application user."""
        user = User(
            name=name.strip(),
            email=email.strip().lower(),
            password_hash=password_hash,
            role=role,
            customer_id=customer_id,
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def list_users(
        self,
        db: Session,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """Query application users with optional role and active filtering."""
        stmt = select(User)
        if role is not None:
            stmt = stmt.where(User.role == role)
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        stmt = stmt.offset(skip).limit(limit)
        return list(db.scalars(stmt).all())


user_repository = UserRepository()
