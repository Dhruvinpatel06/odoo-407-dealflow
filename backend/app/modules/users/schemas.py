"""Pydantic schemas for user administration."""

import uuid
from typing import Optional
from pydantic import BaseModel, Field

from app.common.enums import UserRole
from app.modules.auth.schemas import UserResponse


class UserCreateRequest(BaseModel):
    """Payload for administrative user creation."""

    name: str = Field(..., min_length=1, max_length=255, description="User full name")
    email: str = Field(..., min_length=1, max_length=255, description="User email address")
    password: str = Field(..., min_length=8, description="Password with minimum 8 characters")
    role: UserRole = Field(..., description="Application RBAC role")
    customer_id: Optional[uuid.UUID] = Field(None, description="Associated customer UUID")
    is_active: bool = Field(True, description="Account active status")
