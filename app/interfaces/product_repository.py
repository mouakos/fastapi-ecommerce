"""Interface for Product repository."""

from abc import ABC, abstractmethod
from typing import Literal
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.product import Product
from app.schemas.common import PaginatedRead

allowed_sort_order = Literal["asc", "desc"]
allowed_sort_by = Literal["id", "price", "name", "created_at", "rating", "popularity"]


class ProductRepository(GenericRepository[Product], ABC):
    """Interface for Product repository."""

    @abstractmethod
    async def list_all_paginated(
        self,
        *,
        page: int = 1,
        per_page: int = 10,
        search: str | None = None,
        category_id: UUID | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
        availability: str = "all",
        sort_by: allowed_sort_by = "id",
        sort_order: allowed_sort_order = "asc",
    ) -> PaginatedRead[Product]:
        """Gets a list of products with optional filters, sorting, and pagination.

        Args:
            page (int, optional): Page number for pagination.
            per_page (int, optional): Number of items per page for pagination.
            search (str | None): Search query to filter products by name or description.
            category_id (int | None): Category ID to filter products.
            min_price (float | None): Minimum price to filter products.
            max_price (float | None): Maximum price to filter products.
            min_rating (float | None): Minimum average rating to filter products.
            availability (str | None): Stock availability filter ("in_stock", "out_of_stock", "all").
            sort_by (allowed_sort_by, optional): Field to sort by (e.g., "price", "name", "rating").
            sort_order (allowed_sort_order, optional): Sort order ("asc" or "desc").

        Returns:
            PaginatedRead[Product]: A paginated list of products.
        """

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Product | None:
        """Get a single product by slug.

        Args:
            slug (str): Product slug.

        Returns:
            Product | None: Product or none.
        """
        raise NotImplementedError()

    @abstractmethod
    async def generate_slug(self, name: str) -> str:
        """Generate a unique slug for a product based on its name.

        Args:
            name (str): Product name.

        Returns:
            str: Generated unique slug.
        """
        raise NotImplementedError()

    @abstractmethod
    async def review_count(self, product_id: UUID) -> int:
        """Get the total number of reviews for a product.

        Args:
            product_id (UUID): Product ID.

        Returns:
            int: Total number of reviews.
        """
        raise NotImplementedError()

    @abstractmethod
    async def average_rating(self, product_id: UUID) -> float | None:
        """Get the average rating for a product.

        Args:
            product_id (UUID): Product ID.

        Returns:
            float | None: Average rating or none if no reviews.
        """
        raise NotImplementedError()
