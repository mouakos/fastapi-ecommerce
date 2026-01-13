"""SQL Category repository implementation."""

from slugify import slugify
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.category_repository import CategoryRepository
from app.models.category import Category
from app.repositories.sql_generic_repository import SqlGenericRepository


class SqlCategoryRepository(SqlGenericRepository[Category], CategoryRepository):
    """SQL Category repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, Category)

    async def get_by_slug(self, slug: str) -> Category | None:
        """Get a single category by slug.

        Args:
            slug (str): Category slug.

        Returns:
            Category | None: Category or none.
        """
        stmt = select(Category).where(Category.slug == slug)
        result = await self._session.exec(stmt)
        return result.first()

    async def generate_slug(self, name: str) -> str:
        """Generate a unique slug for a category based on its name.

        Args:
            name (str): Category name.

        Returns:
            str: Generated unique slug.
        """
        base_slug = slugify(name)
        slug = base_slug
        index = 1

        while True:
            stmt = select(Category).where(Category.slug == slug)
            result = await self._session.exec(stmt)
            category = result.first()

            if not category:
                return slug

            slug = f"{base_slug}-{index}"
            index += 1
