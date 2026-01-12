"""SQLModel Product repository implementation."""

from slugify import slugify
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.product_repository import ProductRepository
from app.models.product import Product
from app.repositories.sql_generic_repository import SqlGenericRepository


class SqlProductRepository(SqlGenericRepository[Product], ProductRepository):
    """SQL Product repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, Product)

    async def get_by_slug(self, slug: str) -> Product | None:
        """Get a single product by slug.

        Args:
            slug (str): Product slug.

        Returns:
            Product | None: Product or none.
        """
        stmt = select(Product).where(Product.slug == slug)
        result = await self._session.exec(stmt)
        return result.first()

    async def generate_slug(self, name: str) -> str:
        """Generate a unique slug for a product based on its name.

        Args:
            name (str): Product name.

        Returns:
            str: Generated unique slug.
        """
        base_slug = slugify(name)
        slug = base_slug
        index = 1

        while True:
            stmt = select(Product).where(Product.slug == slug)
            result = await self._session.exec(stmt)
            product = result.first()

            if not product:
                return slug

            slug = f"{base_slug}-{index}"
            index += 1
