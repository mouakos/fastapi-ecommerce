"""Interface for Category repository."""

from abc import ABC, abstractmethod

from app.interfaces.generic_repository import GenericRepository
from app.models.category import Category


class CategoryRepository(GenericRepository[Category], ABC):
    """Interface for Category repository."""

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Category | None:
        """Get a single category by slug.

        Args:
            slug (str): Category slug.

        Returns:
            Category | None: Category or none.
        """
        raise NotImplementedError()

    @abstractmethod
    async def generate_slug(self, name: str) -> str:
        """Generate a unique slug for a category based on its name.

        Args:
            name (str): Category name.

        Returns:
            str: Generated unique slug.
        """
        raise NotImplementedError()
