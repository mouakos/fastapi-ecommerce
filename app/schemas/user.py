"""Schemas for user-related operations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole
from app.schemas.common import UUIDMixin


class UserCreate(BaseModel):
    """Schema for creating user."""

    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=6, max_length=255)
    first_name: str | None = Field(default=None, min_length=2, max_length=50)
    last_name: str | None = Field(default=None, min_length=2, max_length=50)

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "string",
                "first_name": "John",
                "last_name": "Doe",
            }
        },
    )


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    first_name: str | None = Field(None, min_length=2, max_length=50)
    last_name: str | None = Field(None, min_length=2, max_length=50)
    phone_number: str | None = Field(None, max_length=20)

    model_config = ConfigDict(frozen=True)


class UserRead(UUIDMixin):
    """Schema for reading user information."""

    email: EmailStr = Field(..., max_length=255)
    is_superuser: bool
    role: UserRole
    first_name: str | None = Field(..., max_length=50)
    last_name: str | None = Field(..., max_length=50)
    phone_number: str | None = Field(..., max_length=20)

    model_config = ConfigDict(frozen=True)


class UserAdminRead(UserRead):
    """Schema for reading user information in admin context."""

    created_at: datetime
    updated_at: datetime
    total_orders: int = Field(..., description="Total orders by this user")
    total_spent: Decimal = Field(
        ..., description="Total amount spent by this user", ge=0, decimal_places=2, max_digits=10
    )

    model_config = ConfigDict(frozen=True)


class UserAdminRoleUpdate(BaseModel):
    """Schema for updating a user's role."""

    role: UserRole = Field(..., description="New role: 'user' or 'admin'")

    model_config = ConfigDict(frozen=True)


class Login(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str

    model_config = ConfigDict(frozen=True)


class Token(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(frozen=True)


class TokenData(BaseModel):
    """Schema for token data."""

    user_id: UUID

    model_config = ConfigDict(frozen=True)
