"""Schemas for authentication operations."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Login(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str

    model_config = ConfigDict(frozen=True)


class Token(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration time in seconds.")

    model_config = ConfigDict(frozen=True)


class TokenData(BaseModel):
    """Schema for token data."""

    user_id: UUID
    type: Literal["access", "refresh"]
    jti: str = Field(..., description="JWT ID claim for token identification.")
    exp: int = Field(..., description="Expiration time as a UNIX timestamp.")

    model_config = ConfigDict(frozen=True)
