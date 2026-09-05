"""Pydantic schemas for authentication requests and responses."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import UserRole


class LoginRequest(BaseModel):
    """Payload for user login."""

    email: str = Field(..., min_length=1, max_length=255, description="User email address")
    password: str = Field(..., min_length=1, description="Plaintext password")


class SignupRequest(BaseModel):
    """Payload for public customer signup."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., min_length=1, max_length=255, description="Full name")
    email: str = Field(..., min_length=1, max_length=255, description="Email address")
    password: str = Field(..., min_length=8, description="Password with minimum 8 characters")


class TokenResponse(BaseModel):
    """Access token response payload."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration in seconds")


class UserResponse(BaseModel):
    """Authenticated user profile representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    role: UserRole
    customer_id: Optional[uuid.UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ChangePasswordRequest(BaseModel):
    """Payload for changing current user's password."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, description="New password with minimum 8 characters")


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
