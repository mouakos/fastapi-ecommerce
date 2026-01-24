"""Schemas for user-related operations."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole
from app.schemas.common import TwoDecimalBaseModel, UUIDMixin, validate_phone_number


class UserCreate(BaseModel):
    """Schema for creating user."""

    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=6, max_length=255)
    first_name: str | None = Field(default=None, min_length=2, max_length=50)
    last_name: str | None = Field(default=None, min_length=2, max_length=50)
    phone_number: str | None = Field(default=None, max_length=20)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str | None) -> str | None:
        """Validate phone number format using international E.164 standard."""
        return validate_phone_number(v)

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "string",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+4917612345678",
            }
        },
    )


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    first_name: str | None = Field(None, min_length=2, max_length=50)
    last_name: str | None = Field(None, min_length=2, max_length=50)
    phone_number: str | None = Field(None, max_length=20)
    newsletter_subscribed: bool | None = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str | None) -> str | None:
        """Validate phone number format using international E.164 standard."""
        return validate_phone_number(v)

    model_config = ConfigDict(frozen=True)


class UserRoleUpdateRequest(BaseModel):
    """Schema for updating a user's role."""

    role: UserRole = Field(..., description="New role: 'user' or 'admin'")

    model_config = ConfigDict(frozen=True)


class UserPasswordUpdateRequest(BaseModel):
    """Schema for updating user password."""

    old_password: str = Field(..., min_length=6, max_length=255)
    new_password: str = Field(..., min_length=6, max_length=255)
    confirm_password: str = Field(..., min_length=6, max_length=255)

    model_config = ConfigDict(frozen=True)


class UserPublic(UUIDMixin):
    """Schema for reading user information."""

    email: EmailStr
    is_superuser: bool
    role: UserRole
    first_name: str | None
    last_name: str | None
    phone_number: str | None
    newsletter_subscribed: bool
    created_at: datetime
    last_login: datetime | None
    is_active: bool

    model_config = ConfigDict(frozen=True)


class UserAdmin(UserPublic, TwoDecimalBaseModel):
    """Schema for reading user information in admin context."""

    updated_at: datetime
    deleted_at: datetime | None
    total_orders: int
    total_spent: Decimal

    model_config = ConfigDict(frozen=True)


class UserSortByField(StrEnum):
    """Fields to sort users by."""

    EMAIL = "email"
    CREATED_AT = "created_at"


class UserActionResponse(BaseModel):
    """Schema for user action responses."""

    message: str
    user_id: UUID

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "message": "User updated successfully.",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        },
    )
