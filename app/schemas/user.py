"""Schemas for user-related operations."""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import TimestampMixin, UUIDMixin


class UserCreate(BaseModel):
    """Schema for creating user."""

    email: EmailStr
    password: str = Field(..., min_length=6)

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "test@example.com",
                "password": "b4c14256-50ab-495c-bf9c-68eb022e8d8f",
            }
        }
    }


class UserRead(UUIDMixin, TimestampMixin):
    """Schema for reading user information."""

    email: EmailStr
    first_name: str | None
    last_name: str | None
    phone_number: str | None


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    first_name: str | None = Field(None, min_length=2, max_length=50)
    last_name: str | None = Field(None, min_length=2, max_length=50)
    phone_number: str | None = None


class Login(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str = Field(..., min_length=6)


class Token(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str = "bearer"
