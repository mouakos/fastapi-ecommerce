"""Utility functions for building paginated responses with links and metadata."""

from math import ceil
from typing import TypeVar
from urllib.parse import urlencode

from app.schemas.common import PageLinks, PageMeta, PageResponse

T = TypeVar("T")


def _clamp_page_params(page: int, page_size: int, *, max_page_size: int) -> tuple[int, int]:
    page = max(1, int(page))
    page_size = max(1, min(int(page_size), max_page_size))
    return page, page_size


def _build_url(base_path: str, params: dict[str, object]) -> str:
    qs = urlencode({k: v for k, v in params.items() if v is not None})
    return f"{base_path}?{qs}" if qs else base_path


def build_paginated_response[T](
    *,
    items: list[T],
    base_path: str,
    page: int,
    page_size: int,
    total_items: int,
    extra_query: dict[str, object] | None = None,
    max_page_size: int = 100,
) -> PageResponse[T]:
    """Build a PageResponse[T] including PageMeta and PageLinks using page/page_size pagination.

    Args:
        items: Items for the current page.
        base_path: Relative path (e.g. "/api/v1/products").
        page: 1-based page number.
        page_size: Number of items per page.
        total_items: Total number of items across all pages.
        extra_query: Extra query params to include in generated links (e.g. {"sort": "newest"}).
        max_page_size: Maximum allowed page size.

    Returns:
        PageResponse[T]
    """
    extra_query = dict(extra_query or {})
    page, page_size = _clamp_page_params(page, page_size, max_page_size=max_page_size)

    total_items = max(0, int(total_items))
    total_pages = max(1, ceil(total_items / page_size)) if total_items > 0 else 0

    # compute 1-based from/to for UX; use 0/0 when empty
    if total_items == 0:
        from_item = 0
        to_item = 0
    else:
        offset = (page - 1) * page_size
        from_item = min(offset + 1, total_items)
        to_item = min(offset + len(items), total_items)

    # build links
    def url(p: int) -> str:
        params = {"page": p, "page_size": page_size, **extra_query}
        return _build_url(base_path, params)

    if total_pages == 0:
        # empty collection: point everything to page 1
        self_link = url(1)
        links = PageLinks(self=self_link, first=self_link, last=self_link, prev=None, next=None)
    else:
        self_link = url(page)
        first_link = url(1)
        last_link = url(total_pages)
        prev_link = url(page - 1) if page > 1 else None
        next_link = url(page + 1) if page < total_pages else None
        links = PageLinks(
            self=self_link, first=first_link, last=last_link, prev=prev_link, next=next_link
        )

    meta = PageMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        from_item=from_item,
        to_item=to_item,
    )

    return PageResponse[T](items=items, meta=meta, links=links)
