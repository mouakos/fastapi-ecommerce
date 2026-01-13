"""Service for handling review-related operations."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import HTTPException

from app.interfaces.unit_of_work import UnitOfWork
from app.models.review import Review
from app.models.user import UserRole
from app.schemas.review_schema import ReviewCreate, ReviewRead, ReviewUpdate


class ReviewService:
    """Service for handling review-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def create(self, current_user_id: UUID, data: ReviewCreate) -> ReviewRead:
        """Create a new review.

        Args:
            current_user_id (UUID): The ID of the user creating the review.
            data (ReviewCreate): Data for the new review.

        Returns:
            ReviewRead: The created review.
        """
        review_data = data.model_dump()
        new_review = Review(
            user_id=current_user_id,
            **review_data,
        )
        return await self.uow.reviews.add(new_review)

    async def get_by_product(
        self, product_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[ReviewRead]:
        """Get reviews by product ID.

        Args:
            product_id (UUID): The ID of the product.
            skip (int, optional): Number of reviews to skip. Defaults to 0.
            limit (int, optional): Maximum number of reviews to return. Defaults to 100.

        Returns:
            list[ReviewRead]: List of reviews for the product.
        """
        return await self.uow.reviews.get_by_product(product_id, skip=skip, limit=limit)

    async def get_by_id(self, review_id: UUID) -> ReviewRead:
        """Get a review by its ID.

        Args:
            review_id (UUID): The ID of the review.

        Returns:
            ReviewRead: The review with the specified ID.
        """
        review = await self.uow.reviews.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

        return review

    async def update(self, user_id: UUID, review_id: UUID, data: ReviewUpdate) -> ReviewRead:
        """Update a review by its ID.

        Args:
            user_id (UUID): The ID of the current user.
            review_id (UUID): The ID of the review to update.
            data (ReviewUpdate): Updated data for the review.

        Returns:
            ReviewRead: The updated review.
        """
        review = await self.uow.reviews.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

        if review.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this review.")

        review_data = data.model_dump(exclude_unset=True)
        for key, value in review_data.items():
            setattr(review, key, value)

        return await self.uow.reviews.update(review)

    async def delete(self, user_id: UUID, review_id: UUID) -> None:
        """Delete a review by its ID.

        Args:
            user_id (UUID): The ID of the current user.
            review_id (UUID): The ID of the review to delete.
        """
        review = await self.uow.reviews.get_by_id(review_id)

        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

        if review.user_id != user_id and review.user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized to delete this review.")

        await self.uow.reviews.delete_by_id(review_id)
