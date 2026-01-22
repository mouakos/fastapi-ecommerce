"""Interface for Product repository."""

from abc import ABC, abstractmethod
from decimal import Decimal
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.product import Product


class ProductRepository(GenericRepository[Product], ABC):
    """Interface for Product repository."""

    @abstractmethod
    async def find_all(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        category_id: UUID | None = None,
        category_slug: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        min_rating: float | None = None,
        is_active: bool | None = None,
        availability: str = "all",
        sort_by: str = "created_at",
        sort_order: str = "asc",
    ) -> tuple[list[Product], int]:
        """Find all products with optional filters, sorting, and pagination.

        Args:
            page (int, optional): Page number for pagination.
            page_size (int, optional): Number of items per page for pagination.
            search (str | None, optional): Search query to filter products by name or description. Default is None.
            category_id (UUID | None, optional): Category ID to filter products. Default is None.
            category_slug (str | None, optional): Category slug to filter products. Default is None.
            min_price (Decimal | None, optional): Minimum price to filter products. Default is None.
            max_price (Decimal | None, optional): Maximum price to filter products. Default is None.
            min_rating (float | None, optional): Minimum average rating to filter products. Default is None.
            is_active (bool | None, optional): Filter by active status. Default is None.
            availability (str, optional): Stock availability filter ("in_stock", "out_of_stock", "all"). Default is "all".
            sort_by (str, optional): Field to sort by (e.g., "price", "name", "rating"). Default is "created_at".
            sort_order (str, optional): Sort order ("asc" or "desc"). Default is "asc".

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
            limit (int, optional): Maximum number of suggestions to return. Defaults to 10.

        Returns:
            list[str]: List of suggested product names.
        """
        ...

    @abstractmethod
    async def count_low_stock(self, threshold: int = 10) -> int:
        """Count products with stock below specified threshold.

        Args:
            threshold (int): Stock quantity threshold for low stock. Defaults to 10.

        Returns:
            int: Number of products with stock below threshold.
        """
        ...

    @abstractmethod
    async def list_low_stock(
        self,
        *,
        threshold: int = 10,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Product], int]:
        """Find products with stock below specified threshold with pagination.

        Args:
            threshold (int): Stock quantity threshold. Defaults to 10.
            is_active (bool | None): Filter by active status (True, False, or None for all). Defaults to None.
            page (int): Page number for pagination. Defaults to 1.
            page_size (int): Items per page. Defaults to 10.

        Returns:
            tuple[list[Product], int]: List of low stock products and total count.
        """
        ...

    @abstractmethod
    async def list_top_selling(self, limit: int = 10, days: int = 30) -> list[Product]:
        """List top-selling products within specified time frame based on order quantity.

        Args:
            limit (int): Maximum number of products to return. Defaults to 10.
            days (int): Number of days to analyze for sales data. Defaults to 30.

        Returns:
            list[Product]: List of top-selling products ordered by sales volume.
        """
        ...
