"""Auth endpoints router."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.auth.service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Helper to attach the refresh token in a secure, HttpOnly cookie."""
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=token,
        httponly=settings.REFRESH_COOKIE_HTTPONLY,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Helper to remove the refresh token cookie upon logout or password change."""
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path="/",
    )


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Public User Signup",
)
def signup(
    request: SignupRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Public registration endpoint. Automatically creates a CUSTOMER user with is_active=True.
    """
    user = auth_service.signup(db=db, request=request)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
)
def login(

    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate user credentials, start persistent auth session,
    return short-lived access token, and attach refresh token cookie.
    """
    token_response, refresh_token = auth_service.login(db=db, request=request)
    _set_refresh_cookie(response, refresh_token)
    return token_response


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate Refresh Token",
)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Validate refresh token from cookie, rotate refresh token, and return new access token.
    """
    raw_refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    token_response, new_refresh_token = auth_service.refresh(
        db=db, raw_refresh_token=raw_refresh_token
    )
    _set_refresh_cookie(response, new_refresh_token)
    return token_response


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="User Logout",
)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Revoke current refresh session and clear the refresh token cookie.
    """
    raw_refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    auth_service.logout(db=db, raw_refresh_token=raw_refresh_token)
    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Return authenticated user profile without exposing credentials or sensitive tokens.
    """
    return UserResponse.model_validate(current_user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change User Password",
)
def change_password(
    request: ChangePasswordRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Verify current password, store new Argon2id hash, and revoke existing sessions.
    """
    auth_service.change_password(db=db, user=current_user, request=request)
    _clear_refresh_cookie(response)
    return MessageResponse(message="Password changed successfully")
