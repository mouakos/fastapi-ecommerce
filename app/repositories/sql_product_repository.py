"""SQL Product repository implementation."""

from uuid import UUID

from slugify import slugify
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.product_repository import ProductRepository
from app.models.product import Product
from app.models.review import Review
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

    async def review_count(self, product_id: UUID) -> int:
        """Get the total number of reviews for a product.

        Args:
            product_id (UUID): Product ID.

        Returns:
            int: Total number of reviews.
        """
        stmt = select(func.count()).select_from(Review).where(Review.product_id == product_id)
        result = await self._session.exec(stmt)
        return result.first() or 0

    async def average_rating(self, product_id: UUID) -> float | None:
        """Get the average rating for a product.

        Args:
            product_id (UUID): Product ID.

        Returns:
            float | None: Average rating or none if no reviews.
        """
        stmt = select(func.avg(Review.rating)).where(Review.product_id == product_id)
        result = await self._session.exec(stmt)
        avg_rating = result.first()
        return float(avg_rating) if avg_rating is not None else None
