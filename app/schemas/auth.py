"""Schemas for authentication operations."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.security import TokenType


class Token(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration time in seconds.")

    model_config = ConfigDict(frozen=True)


class TokenData(BaseModel):
    """Schema for token data."""

    user_id: UUID
    type: TokenType
    jti: str = Field(..., description="JWT ID claim for token identification.")
    exp: int = Field(..., description="Expiration time as a UNIX timestamp.")

    model_config = ConfigDict(frozen=True)
