"""Business logic and workflow orchestration for manual authentication."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.config import settings
from app.core.exceptions import DealFlowException, UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User
from app.modules.auth.repository import auth_repository
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    SignupRequest,
    TokenResponse,
)
from app.modules.users.repository import user_repository


class AuthService:
    """Coordinates authentication workflows, token lifecycles, and session state."""

    def signup(self, db: Session, request: SignupRequest) -> User:
        """
        Public customer signup workflow.
        Always assigns role=CUSTOMER, active=True, and customer_id=None.
        Rejects duplicate emails and hashes password with Argon2id.
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
            role=UserRole.CUSTOMER,
            customer_id=None,
            is_active=True,
        )

    def login(self, db: Session, request: LoginRequest) -> Tuple[TokenResponse, str]:
        """Authenticate user credentials, initiate session, and return access/refresh tokens."""
        user = auth_repository.get_user_by_email(db, request.email)
        if not user or not verify_password(request.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("User account is inactive")

        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        access_token = create_access_token(user.id, role_str)

        raw_refresh_token = generate_refresh_token()
        refresh_token_hash = hash_refresh_token(raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        auth_repository.create_auth_session(
            db=db,
            user_id=user.id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
        )

        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return token_response, raw_refresh_token

    def refresh(
        self, db: Session, raw_refresh_token: Optional[str]
    ) -> Tuple[TokenResponse, str]:
        """Validate session from refresh token, rotate refresh token, and return new access token."""
        if not raw_refresh_token:
            raise UnauthorizedError("Refresh token missing")

        token_hash = hash_refresh_token(raw_refresh_token)
        session = auth_repository.get_auth_session_by_token_hash(db, token_hash)
        if not session:
            raise UnauthorizedError("Invalid refresh session")

        if session.revoked_at is not None:
            raise UnauthorizedError("Session has been revoked")

        session_expires_at = session.expires_at
        if session_expires_at.tzinfo is None:
            session_expires_at = session_expires_at.replace(tzinfo=timezone.utc)

        if session_expires_at <= datetime.now(timezone.utc):
            raise UnauthorizedError("Session has expired")

        user = auth_repository.get_user_by_id(db, session.user_id)
        if not user:
            raise UnauthorizedError("User not found")

        if not user.is_active:
            raise UnauthorizedError("User account is inactive")

        new_raw_refresh_token = generate_refresh_token()
        new_token_hash = hash_refresh_token(new_raw_refresh_token)
        new_expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        auth_repository.rotate_auth_session(
            db=db,
            session=session,
            new_refresh_token_hash=new_token_hash,
            new_expires_at=new_expires_at,
        )

        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        new_access_token = create_access_token(user.id, role_str)

        token_response = TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return token_response, new_raw_refresh_token

    def logout(self, db: Session, raw_refresh_token: Optional[str]) -> None:
        """Revoke the current authentication session if present."""
        if raw_refresh_token:
            token_hash = hash_refresh_token(raw_refresh_token)
            session = auth_repository.get_auth_session_by_token_hash(db, token_hash)
            if session and session.revoked_at is None:
                auth_repository.revoke_auth_session(db, session)

    def change_password(
        self, db: Session, user: User, request: ChangePasswordRequest
    ) -> None:
        """Verify current password, update to new Argon2id hash, and revoke existing sessions."""
        if not verify_password(request.current_password, user.password_hash):
            raise UnauthorizedError("Current password is incorrect")

        new_hash = hash_password(request.new_password)
        auth_repository.update_user_password(db, user, new_hash)
        auth_repository.revoke_all_user_sessions(db, user.id)

    def signup(self, db: Session, request: SignupRequest) -> User:
        """Register a new customer account."""
        email_clean = request.email.strip().lower()
        existing = auth_repository.get_user_by_email(db, email_clean)
        if existing:
            raise DealFlowException("Email already registered", status_code=400)

        hashed_pwd = hash_password(request.password)
        new_user = User(
            name=request.name.strip(),
            email=email_clean,
            password_hash=hashed_pwd,
            role=UserRole.CUSTOMER,
            is_active=True,
            customer_id=None,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user


auth_service = AuthService()

