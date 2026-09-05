"""Pydantic schemas for users module."""

import uuid
from typing import Optional

from pydantic import BaseModel, Field

from app.common.enums import UserRole
from app.modules.auth.schemas import UserResponse


class UserCreateRequest(BaseModel):
    """Payload for administrative user creation."""

    name: str = Field(..., min_length=1, max_length=255, description="Full name")
    email: str = Field(..., min_length=1, max_length=255, description="Email address")
    password: str = Field(..., min_length=8, description="Password with minimum 8 characters")
    role: UserRole = Field(..., description="Application role assigned to user")
    customer_id: Optional[uuid.UUID] = Field(None, description="Optional customer account linkage")
    is_active: bool = Field(True, description="Whether the user is active")


__all__ = ["UserCreateRequest", "UserResponse"]
