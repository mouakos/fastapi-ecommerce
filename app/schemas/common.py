"""Common Pydantic Schemas."""

from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UUIDMixin(BaseModel):
    """Mixin to add a UUID primary key."""

    id: UUID


T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    current_page: int = Field(..., description="Current page number (1-based)")
    per_page: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    total_items: int = Field(..., description="Total number of items across all pages")
    from_item: int | None = Field(None, description="Starting item index (1-based)")
    to_item: int | None = Field(None, description="Ending item index (1-based)")

    model_config = ConfigDict(frozen=True)


class PaginationLinks(BaseModel):
    """HATEOAS links for pagination."""

    self: str | None = Field(None, description="URL to the current page")
    first: str | None = Field(None, description="URL to the first page")
    prev: str | None = Field(None, description="URL to the previous page, or null if none")
    next: str | None = Field(None, description="URL to the next page, or null if none")
    last: str | None = Field(None, description="URL to the last page")

    model_config = ConfigDict(frozen=True)


class PaginatedRead[T](BaseModel):
    """Generic paginated response schema."""

    data: list[T] = Field(..., description="List of items for the current page")
    meta: PaginationMeta = Field(..., description="Pagination metadata")
    links: PaginationLinks | None = Field(None, description="HATEOAS links for navigation")

    model_config = ConfigDict(frozen=True)
