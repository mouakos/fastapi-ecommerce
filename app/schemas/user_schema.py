"""Schemas for user-related operations."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import UUIDMixin


class UserCreate(BaseModel):
    """Schema for creating user."""

    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "string",
                "first_name": "John",
                "last_name": "Doe",
            }
        }
    }


class UserRead(UUIDMixin):
    """Schema for reading user information."""

    email: EmailStr
    first_name: str
    last_name: str
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


class TokenData(BaseModel):
    """Schema for token data."""

    user_id: UUID
