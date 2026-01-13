"""Interface for Product repository."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.review import Review


class ReviewRepository(GenericRepository[Review], ABC):
    """Interface for Review repository."""

    @abstractmethod
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
        raise NotImplementedError()
