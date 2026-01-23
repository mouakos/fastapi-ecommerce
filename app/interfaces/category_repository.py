"""Interface for Category repository."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.category import Category


class CategoryRepository(GenericRepository[Category], ABC):
    """Interface for Category repository."""

    @abstractmethod
    async def find_category_detail_by_id(self, category_id: UUID) -> Category | None:
        """Find a category by ID, including its hierarchy.

        Args:
            category_id (UUID): Category ID.

        Returns:
            Category | None: Category or none, including its hierarchy.
        """
        ...

    @abstractmethod
    async def find_category_detail_by_slug(self, slug: str) -> Category | None:
        """Find a category by slug, including its hierarchy.

        Args:
            slug (str): Category slug.

        Returns:
            Category | None: Category or none, including its hierarchy.
        """
        ...

    @abstractmethod
    async def generate_slug(self, name: str) -> str:
        """Generate a unique slug for a category based on its name.

        Args:
            name (str): Category name.

        Returns:
            str: Generated unique slug.
        """
        ...
