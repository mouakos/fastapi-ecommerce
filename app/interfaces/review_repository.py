"""Interface for Product repository."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.review import Review, ReviewStatus


class ReviewRepository(GenericRepository[Review], ABC):
    """Interface for Review repository."""

    @abstractmethod
    async def find_user_review(self, review_id: UUID, user_id: UUID) -> Review | None:
        """Find a review by its ID and user ID.

        Args:
            review_id (UUID): Review ID.
            user_id (UUID): User ID.

        Returns:
            Review | None: Review or none.
        """
        ...

    @abstractmethod
    async def find_user_product_review(self, user_id: UUID, product_id: UUID) -> Review | None:
        """Find a review by user ID and product ID.

        Args:
            user_id (UUID): User ID.
            product_id (UUID): Product ID.

        Returns:
            Review | None: Review or none.
        """
        ...

    @abstractmethod
    async def count(
        self,
        product_id: UUID | None = None,
        status: ReviewStatus | None = None,
        user_id: UUID | None = None,
        rating: int | None = None,
    ) -> int:
        """Get the total number of reviews with optional filters.

        Args:
            product_id (UUID | None, optional): Filter by product ID. Defaults to None.
            status (ReviewStatus | None, optional): Filter by review status. Defaults to None.
            user_id (UUID | None, optional): Filter by user ID. Defaults to None.
            rating (int | None, optional): Filter by rating. Defaults to None.

        Returns:
            int: Total number of reviews.
        """
        ...

    @abstractmethod
    async def calculate_average_rating(self) -> float:
        """Calculate the average rating of all reviews.

        Returns:
            float: Average rating.
        """
        ...

    @abstractmethod
    async def find_approved_review(self, review_id: UUID) -> Review | None:
        """Find an approved review by its ID.

        Args:
            review_id (UUID): Review ID.

        Returns:
            Review | None: Review or none.
        """
        ...

    @abstractmethod
    async def paginate(
        self,
        page: int = 1,
        page_size: int = 10,
        product_id: UUID | None = None,
        status: ReviewStatus | None = None,
        user_id: UUID | None = None,
        rating: int | None = None,
    ) -> tuple[int, list[Review]]:
        """Get paginated reviews with optional filters.

        Args:
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 10.
            product_id (UUID | None, optional): Filter by product ID. Defaults to None.
            status (ReviewStatus | None, optional): Filter by review status. Defaults to None.
            user_id (UUID | None, optional): Filter by user ID. Defaults to None.
            rating (int | None, optional): Filter by rating. Defaults to None.

        Returns:
            tuple[int, list[Review]]: Total count and list of reviews.
        """
        ...
