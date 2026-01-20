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
    async def calculate_average_rating(self) -> float:
        """Calculate the average rating of all reviews.

        Returns:
            float: Average rating.
        """
        ...

    @abstractmethod
    async def paginate(
        self,
        *,
        product_id: UUID | None = None,
        status: ReviewStatus | None = None,
        user_id: UUID | None = None,
        rating: int | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Review], int]:
        """Paginate reviews with optional filters.

        Args:
            product_id (UUID | None, optional): Filter by product ID. Defaults to None.
            status (ReviewStatus | None, optional): Filter by review status. Defaults to None.
            user_id (UUID | None, optional): Filter by user ID. Defaults to None.
            rating (int | None, optional): Filter by rating. Defaults to None.
            sort_by (str, optional): Field to sort by. Defaults to "created_at".
            sort_order (str, optional): Sort order. Defaults to "desc".
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 10.


        Returns:
            tuple[list[Review], int]: List of reviews and total count.
        """
        ...
