"""Interface for Product repository."""

from abc import ABC, abstractmethod

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
