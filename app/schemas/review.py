"""Schemas for review operations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.review import ReviewStatus
from app.schemas.common import UUIDMixin


class ReviewBase(BaseModel):
    """Base schema for review."""

    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ReviewCreate(ReviewBase):
    """Schema for creating a review."""

    product_id: UUID

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "product_id": "123e4567-e89b-12d3-a456-426614174000",
                "rating": 5,
                "comment": "Great product! Highly recommend.",
            }
        },
    )


class ReviewUpdate(BaseModel):
    """Schema for updating a review."""

    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)

    model_config = ConfigDict(frozen=True)


class ReviewRead(ReviewBase, UUIDMixin):
    """Schema for reading a review."""

    status: ReviewStatus
    user_id: UUID
    product_id: UUID
    created_at: datetime

    model_config = ConfigDict(frozen=True)


class ReviewAdminRead(UUIDMixin):
    """Schema for reading review information in admin context."""

    user_id: UUID
    user_email: str
    product_id: UUID
    product_name: str
    rating: int = Field(ge=1, le=5)
    comment: str | None
    created_at: datetime
    updated_at: datetime
    status: ReviewStatus

    model_config = ConfigDict(frozen=True)
