"""Interface for Product repository."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.review import Review


class ReviewRepository(GenericRepository[Review], ABC):
    """Interface for Review repository."""

    @abstractmethod
    async def get_by_id_and_user_id(self, review_id: UUID, user_id: UUID) -> Review | None:
        """Get a review by its ID and user ID.

        Args:
            review_id (UUID): Review ID.
            user_id (UUID): User ID.

        Returns:
            Review | None: Review or none.
        """
        ...

    @abstractmethod
    async def get_by_user_id_and_product_id(self, user_id: UUID, product_id: UUID) -> Review | None:
        """Get a review by user ID and product ID.

        Args:
            user_id (UUID): User ID.
            product_id (UUID): Product ID.

        Returns:
            Review | None: Review or none.
        """
        ...

    @abstractmethod
    async def count_all(self, **filters: Any) -> int:  # noqa: ANN401
        """Get total number of reviews.

        Args:
            **filters: Filter conditions.

        Returns:
            int: Total number of reviews.

        Raises:
            ValueError: If invalid filters are provided.
        """
        ...

    @abstractmethod
    async def get_average_rating(self) -> float | None:
        """Get the average rating for all reviews.

        Returns:
            float | None: Average rating or none if no reviews.
        """
        ...

    @abstractmethod
    async def get_all_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        product_id: UUID | None = None,
        is_approved: bool | None = None,
        user_id: UUID | None = None,
        rating: int | None = None,
    ) -> tuple[int, list[Review]]:
        """Get all reviews with pagination and optional filters.

        Args:
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 100.
            product_id (UUID | None, optional): Filter by product ID. Defaults to None.
            is_approved (bool | None, optional): Filter by approval status. Defaults to None.
            user_id (UUID | None, optional): Filter by user ID. Defaults to None.
            rating (int | None, optional): Filter by rating. Defaults to None.

        Returns:
            tuple[int, list[Review]]: Total count and list of reviews.
        """
        ...
