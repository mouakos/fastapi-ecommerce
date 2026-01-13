"""Interface for Product repository."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.product import Product


class ProductRepository(GenericRepository[Product], ABC):
    """Interface for Product repository."""

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
