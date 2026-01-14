"""Interface for Product repository."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.review import Review


class ReviewRepository(GenericRepository[Review], ABC):
    """Interface for Review repository."""

    @abstractmethod
    async def get_by_product(
        self, product_id: UUID, skip: int = 0, limit: int = 10
    ) -> list[Review]:
        """Get all reviews for a specific product.

        Args:
            product_id (UUID): Product ID.
            skip (int, optional): Number of reviews to skip. Defaults to 0.
            limit (int, optional): Maximum number of reviews to return. Defaults to 10.

        Returns:
            list[Review]: List of reviews.
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

    @abstractmethod
    async def get_average_rating(self) -> float | None:
        """Get the average rating for all reviews.

        Returns:
            float | None: Average rating or none if no reviews.
        """
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()
