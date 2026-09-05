"""Repository for user credentials and auth_sessions persistence."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.auth_session import AuthSession
from app.models.user import User


class AuthRepository:
    """Encapsulates database operations for users and auth_sessions."""

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        stmt = select(User).where(func.lower(User.email) == email.strip().lower())
        return db.scalars(stmt).first()

    def get_user_by_id(self, db: Session, user_id: uuid.UUID) -> Optional[User]:
        return db.get(User, user_id)

    def update_user_password(self, db: Session, user: User, password_hash: str) -> User:
        user.password_hash = password_hash
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def create_auth_session(
        self,
        db: Session,
        user_id: uuid.UUID,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> AuthSession:
        session = AuthSession(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            last_used_at=datetime.now(timezone.utc),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_auth_session_by_token_hash(
        self, db: Session, refresh_token_hash: str
    ) -> Optional[AuthSession]:
        stmt = select(AuthSession).where(
            AuthSession.refresh_token_hash == refresh_token_hash
        )
        return db.scalars(stmt).first()

    def rotate_auth_session(
        self,
        db: Session,
        session: AuthSession,
        new_refresh_token_hash: str,
        new_expires_at: datetime,
    ) -> AuthSession:
        session.refresh_token_hash = new_refresh_token_hash
        session.expires_at = new_expires_at
        session.last_used_at = datetime.now(timezone.utc)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def revoke_auth_session(self, db: Session, session: AuthSession) -> None:
        session.revoked_at = datetime.now(timezone.utc)
        db.add(session)
        db.commit()

    def revoke_all_user_sessions(self, db: Session, user_id: uuid.UUID) -> int:
        now = datetime.now(timezone.utc)
        stmt = (
            update(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount


auth_repository = AuthRepository()
