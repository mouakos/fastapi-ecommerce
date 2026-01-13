"""SQL Review repository implementation."""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.review_repository import ReviewRepository
from app.models.review import Review
from app.repositories.sql_generic_repository import SqlGenericRepository


class SqlReviewRepository(SqlGenericRepository[Review], ReviewRepository):
    """SQL Review repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, Review)

    async def get_by_product(
        self, product_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Review]:
        """Get all reviews for a specific product.

        Args:
            product_id (UUID): Product ID.
            skip (int, optional): Number of reviews to skip. Defaults to 0.
            limit (int, optional): Maximum number of reviews to return. Defaults to 100.

        Returns:
            list[Review]: List of reviews.
        """
        stmt = select(Review).where(Review.product_id == product_id).offset(skip).limit(limit)
        result = await self._session.exec(stmt)
        return list(result.all())
