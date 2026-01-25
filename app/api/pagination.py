"""Utility functions for building paginated responses with links and metadata."""

from math import ceil
from typing import TypeVar

from app.schemas.common import Page

T = TypeVar("T")


def build_page[T](
    *,
    items: list[T],
    page: int,
    size: int,
    total: int,
) -> Page[T]:
    """Build a Page[T] object.

    Args:
        items: Items for the current page.
        page: 1-based page number.
        size: Number of items per page.
        total: Total number of items across all pages.

    Returns:
        Page[T]
    """
    total = max(0, int(total))
    total_pages = max(1, ceil(total / size)) if total > 0 else 0

    return Page[T](items=items, total=total, page=page, size=size, pages=total_pages)
