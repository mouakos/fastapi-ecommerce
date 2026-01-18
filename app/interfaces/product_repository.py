"""Interface for Product repository."""

from abc import ABC, abstractmethod
from typing import Literal
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.product import Product

allowed_sort_order = Literal["asc", "desc"]
allowed_sort_by = Literal["id", "price", "name", "created_at", "rating", "popularity"]


class ProductRepository(GenericRepository[Product], ABC):
    """Interface for Product repository."""

    @abstractmethod
    async def paginate(
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
    ) -> tuple[list[Product], int]:
        """List all products with pagination and optional filters.

        Args:
            page (int, optional): Page number for pagination.
            per_page (int, optional): Number of items per page for pagination.
            search (str | None): Search query to filter products by name or description.
            category_id (UUID | None): Category ID to filter products.
            min_price (float | None): Minimum price to filter products.
            max_price (float | None): Maximum price to filter products.
            min_rating (float | None): Minimum average rating to filter products.
            availability (str | None): Stock availability filter ("in_stock", "out_of_stock", "all").
            sort_by (allowed_sort_by, optional): Field to sort by (e.g., "price", "name", "rating").
            sort_order (allowed_sort_order, optional): Sort order ("asc" or "desc").

        Returns:
            tuple[list[Product], int]: A tuple containing a list of products and the total number of products.
        """
        ...

    @abstractmethod
    async def find_by_slug(self, slug: str) -> Product | None:
        """Find a single product by slug.

        Args:
            slug (str): Product slug.

        Returns:
            Product | None: Product or none.
        """
        ...

    @abstractmethod
    async def generate_slug(self, name: str) -> str:
        """Generate a unique slug for a product based on its name.

        Args:
            name (str): Product name.

        Returns:
            str: Generated unique slug.
        """
        ...

    @abstractmethod
    async def count_reviews(self, product_id: UUID) -> int:
        """Count the total number of reviews for a product.

        Args:
            product_id (UUID): Product ID.

        Returns:
            int: Total number of reviews.
        """
        ...

    @abstractmethod
    async def calculate_average_rating(self, product_id: UUID) -> float | None:
        """Calculate the average rating for a product.

        Args:
            product_id (UUID): Product ID.

        Returns:
            float | None: Average rating or none if no reviews.
        """
        ...

    @abstractmethod
    async def list_autocomplete_suggestions(self, query: str, limit: int = 10) -> list[str]:
        """List autocomplete suggestions for product names based on a search query.

        Args:
            query (str): Search query.
            limit (int, optional): Maximum number of suggestions to return. Defaults to 5.

        Returns:
            list[str]: List of suggested product names.
        """
        ...

    @abstractmethod
    async def list_by_category_slug(
        self, category_slug: str, page: int = 1, page_size: int = 10
    ) -> tuple[list[Product], int]:
        """List products by category slug.

        Args:
            category_slug (str): Category slug.
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of products per page. Defaults to 10.

        Returns:
            tuple[list[Product], int]: List of products in the specified category and total count.
        """
        ...

    @abstractmethod
    async def list_by_category_id(
        self, category_id: UUID, page: int = 1, page_size: int = 10
    ) -> tuple[list[Product], int]:
        """List products by category ID.

        Args:
            category_id (UUID): Category ID.
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of products per page. Defaults to 10.

        Returns:
            tuple[list[Product], int]: List of products in the specified category and total count.
        """
        ...

    @abstractmethod
    async def count_low_stock(self, threshold: int = 10) -> int:
        """Count number of products that are low in stock.

        Args:
            threshold (int): Stock threshold.

        Returns:
            int: Number of products that are low in stock.
        """
        ...

    @abstractmethod
    async def list_low_stock(
        self, threshold: int = 10, page: int = 1, page_size: int = 10
    ) -> tuple[list[Product], int]:
        """List products that are low in stock.

        Args:
            threshold (int): Stock threshold.
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of products per page. Defaults to 10.

        Returns:
            tuple[list[Product], int]: List of low stock products and total count.
        """
        ...

    @abstractmethod
    async def list_top_selling(self, limit: int = 10, days: int = 30) -> list[Product]:
        """List top selling products within a specified time frame.

        Args:
            limit (int): Number of top selling products to retrieve.
            days (int): Number of days to consider for sales data.

        Returns:
            list[Product]: List of top selling products.
        """
        ...
