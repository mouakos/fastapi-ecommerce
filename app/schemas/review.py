"""Schemas for review operations."""

from datetime import datetime
from enum import StrEnum
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


class ReviewPublic(ReviewBase, UUIDMixin):
    """Schema for reading a review."""

    user_id: UUID
    product_id: UUID
    status: ReviewStatus
    created_at: datetime

    model_config = ConfigDict(frozen=True)


class ReviewAdmin(ReviewPublic):
    """Schema for reading review information in admin context."""

    user_email: str = Field(..., max_length=255)
    product_name: str = Field(..., max_length=255)
    moderated_at: datetime | None
    moderated_by: UUID | None
    updated_at: datetime

    model_config = ConfigDict(frozen=True)


class ReviewSortByField(StrEnum):
    """Fields to sort product reviews by."""

    RATING = "rating"
    CREATED_AT = "created_at"


class ReviewActionResponse(BaseModel):
    """Schema for review action responses."""

    message: str
    review_id: UUID

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Review submitted successfully.",
                "review_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }
    )
