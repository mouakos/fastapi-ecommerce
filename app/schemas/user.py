"""Schemas for user-related operations."""

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


class UserRead(UUIDMixin):
    """Schema for reading user information."""

    email: EmailStr
    is_superuser: bool
    role: UserRole
    first_name: str | None
    last_name: str | None
    phone_number: str | None

    model_config = ConfigDict(frozen=True)


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    first_name: str | None = Field(None, min_length=2, max_length=50)
    last_name: str | None = Field(None, min_length=2, max_length=50)
    phone_number: str | None = Field(None, max_length=20)

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
