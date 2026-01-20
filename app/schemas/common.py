"""Common Pydantic Schemas."""

from enum import StrEnum
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class UUIDMixin(BaseModel):
    """Mixin to add a UUID primary key."""

    id: UUID

    model_config = ConfigDict(frozen=True)


class Page[T](BaseModel):
    """Pagination information."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(frozen=True)


class SortOrder(StrEnum):
    """Sorting order."""

    ASC = "asc"
    DESC = "desc"
