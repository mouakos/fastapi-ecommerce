"""SQL Review repository implementation."""

from uuid import UUID

from sqlalchemy import func
from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.review_repository import ReviewRepository
from app.models.review import Review, ReviewStatus
from app.repositories.sql_generic_repository import SqlGenericRepository


class SqlReviewRepository(SqlGenericRepository[Review], ReviewRepository):
    """SQL Review repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, Review)

    async def find_user_review(self, review_id: UUID, user_id: UUID) -> Review | None:
        """Find a review by its ID and user ID.

        Args:
            review_id (UUID): Review ID.
            user_id (UUID): User ID.

        Returns:
            Review | None: Review or none.
        """
        stmt = select(Review).where((Review.id == review_id) & (Review.user_id == user_id))
        result = await self._session.exec(stmt)
        return result.first()

    async def find_approved_review(self, review_id: UUID) -> Review | None:
        """Find an approved review by its ID.

        Args:
            review_id (UUID): Review ID.

        Returns:
            Review | None: Review or none.
        """
        stmt = select(Review).where(
            (Review.id == review_id) & (Review.status == ReviewStatus.APPROVED)
        )
        result = await self._session.exec(stmt)
        return result.first()

    async def find_user_product_review(self, user_id: UUID, product_id: UUID) -> Review | None:
        """Find a review by user ID and product ID.

        Args:
            user_id (UUID): User ID.
            product_id (UUID): Product ID.

        Returns:
            Review | None: Review or none.
        """
        stmt = select(Review).where((Review.user_id == user_id) & (Review.product_id == product_id))
        result = await self._session.exec(stmt)
        return result.first()

    async def count(
        self,
        product_id: UUID | None = None,
        status: ReviewStatus | None = None,
        user_id: UUID | None = None,
        rating: int | None = None,
    ) -> int:
        """Count total number of reviews.

        Args:
            product_id (UUID | None, optional): Filter by product ID. Defaults to None.
            status (ReviewStatus | None, optional): Filter by review status. Defaults to None.
            user_id (UUID | None, optional): Filter by user ID. Defaults to None.
            rating (int | None, optional): Filter by rating. Defaults to None.

        Returns:
            int: Total number of reviews.
        """
        stmt = select(func.count()).select_from(Review)

        if product_id is not None:
            stmt = stmt.where(Review.product_id == product_id)
        if status is not None:
            stmt = stmt.where(Review.status == status)
        if user_id is not None:
            stmt = stmt.where(Review.user_id == user_id)
        if rating is not None:
            stmt = stmt.where(Review.rating == rating)

        result = await self._session.exec(stmt)
        return result.first() or 0

    async def calculate_average_rating(self) -> float:
        """Calculate the average rating of all reviews.

        Returns:
            float: Average rating or 0 if no reviews.
        """
        stmt = select(func.avg(Review.rating))
        result = await self._session.exec(stmt)
        average = result.first()
        return float(average) if average is not None else 0

    async def paginate(
        self,
        page: int = 1,
        page_size: int = 10,
        product_id: UUID | None = None,
        status: ReviewStatus | None = None,
        user_id: UUID | None = None,
        rating: int | None = None,
    ) -> tuple[int, list[Review]]:
        """Get all reviews with pagination and optional filters.

        Args:
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 100.
            product_id (UUID | None, optional): Filter by product ID. Defaults to None.
            status (ReviewStatus | None, optional): Filter by review status. Defaults to None.
            user_id (UUID | None, optional): Filter by user ID. Defaults to None.
            rating (int | None, optional): Filter by rating. Defaults to None.

        Returns:
            tuple[int, list[Review]]: Total count and list of reviews.
        """
        # Build the query
        stmt = select(Review)

        # Apply filters
        if product_id is not None:
            stmt = stmt.where(Review.product_id == product_id)
        if status is not None:
            stmt = stmt.where(Review.status == status)
        if user_id is not None:
            stmt = stmt.where(Review.user_id == user_id)
        if rating is not None:
            stmt = stmt.where(Review.rating == rating)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self._session.exec(count_stmt)
        total = count_result.first() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        # Execute query
        result = await self._session.exec(stmt.order_by(desc(Review.created_at)))
        reviews = list(result.all())

        return total, reviews
