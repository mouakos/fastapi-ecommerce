"""SQL Review repository implementation."""

from typing import Any
from uuid import UUID

from sqlalchemy import func
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

    async def count_all(self, **filters: Any) -> int:  # noqa: ANN401
        """Get total number of reviews.

        Args:
            **filters: Filter conditions.

        Returns:
            int: Total number of reviews.

        Raises:
            ValueError: If invalid filters are provided.
        """
        stmt = select(func.count()).select_from(Review)

        for attr, value in filters.items():
            if not hasattr(Review, attr):
                raise ValueError(f"Invalid filter condition: {attr}")
            stmt = stmt.where(getattr(Review, attr) == value)

        result = await self._session.exec(stmt)
        return result.first() or 0

    async def get_average_rating(self) -> float:
        """Get the average rating for all reviews.

        Returns:
            float: Average rating or 0 if no reviews.
        """
        stmt = select(func.avg(Review.rating))
        result = await self._session.exec(stmt)
        average = result.first()
        return float(average) if average is not None else 0

    async def get_all_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        product_id: UUID | None = None,
        is_approved: bool | None = None,
    ) -> tuple[int, list[Review]]:
        """Get all reviews with pagination and optional filters.

        Args:
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 100.
            product_id (UUID | None, optional): Filter by product ID. Defaults to None.
            is_approved (bool | None, optional): Filter by approval status. Defaults to None.

        Returns:
            tuple[int, list[Review]]: Total count and list of reviews.
        """
        # Build the query
        stmt = select(Review)

        # Apply filters
        if product_id is not None:
            stmt = stmt.where(Review.product_id == product_id)
        if is_approved is not None:
            stmt = stmt.where(Review.is_approved == is_approved)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self._session.exec(count_stmt)
        total = count_result.first() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        # Execute query
        result = await self._session.exec(stmt)
        reviews = list(result.all())

        return total, reviews
