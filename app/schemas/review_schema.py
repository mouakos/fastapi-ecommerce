"""Schemas for review operations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import UUIDMixin


class ReviewBase(BaseModel):
    """Base schema for review."""

    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ReviewCreate(ReviewBase):
    """Schema for creating a review."""

    product_id: UUID

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": "123e4567-e89b-12d3-a456-426614174000",
                "rating": 5,
                "comment": "Great product! Highly recommend.",
            }
        }
    )


class ReviewUpdate(BaseModel):
    """Schema for updating a review."""

    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ReviewRead(ReviewBase, UUIDMixin):
    """Schema for reading a review."""

    is_approved: bool
    user_id: UUID
    product_id: UUID
    created_at: datetime
