"""Service for handling review-related operations."""

from uuid import UUID

from fastapi import HTTPException

from app.interfaces.unit_of_work import UnitOfWork
from app.models.review import Review, ReviewStatus
from app.schemas.review import ReviewCreate, ReviewUpdate


class ReviewService:
    """Service for handling review-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def create_review(self, user_id: UUID, data: ReviewCreate) -> Review:
        """Create a new product review with PENDING status.

        Args:
            user_id (UUID): ID of the user creating the review.
            data (ReviewCreate): Review data including rating (1-5) and optional comment.

        Returns:
            Review: The created review with PENDING status awaiting admin approval.

        Raises:
            HTTPException: If product does not exist or user has already reviewed the product.
        """
        product = await self.uow.products.find_by_id(data.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        existing = await self.uow.reviews.find_user_product_review(user_id, data.product_id)
        if existing:
            raise HTTPException(status_code=400, detail="You have already reviewed this product.")

        review_data = data.model_dump()
        new_review = Review(
            user_id=user_id,
            **review_data,
            status=ReviewStatus.PENDING,
        )
        return await self.uow.reviews.add(new_review)

    async def get_product_reviews(
        self,
        *,
        product_id: UUID,
        rating: int | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Review], int]:
        """List reviews for a specific product.

        Args:
            product_id (UUID): The ID of the product.
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of reviews per page. Defaults to 10.
            rating (int | None, optional): Filter reviews by rating. Defaults to None.
            sort_by (str, optional): Field to sort by. Defaults to "created_at".
            sort_order (str, optional): Sort order ("asc" or "desc"). Defaults to "desc".

        Returns:
            tuple[list[Review], int]: List of reviews and total count for the product.

        Raises:
            HTTPException: If the product does not exist.
        """
        product = await self.uow.products.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        total, reviews = await self.uow.reviews.find_all(
            page=page,
            page_size=page_size,
            status=ReviewStatus.APPROVED,
            product_id=product_id,
            rating=rating,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return total, reviews

    async def get_review(self, review_id: UUID, user_id: UUID) -> Review:
        """Get a review.

        Args:
            review_id (UUID): The ID of the review.
            user_id (UUID): The ID of the current user.

        Returns:
            Review: The review with the specified ID.

        Raises:
            HTTPException: If the review is not found or not approved.
        """
        review = await self.uow.reviews.find_user_review(review_id, user_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

        return review

    async def update_review(self, review_id: UUID, user_id: UUID, data: ReviewUpdate) -> Review:
        """Update a review and reset approval status to PENDING.

        Args:
            review_id (UUID): ID of the review to update.
            user_id (UUID): ID of the user (must be review author).
            data (ReviewUpdate): Updated rating or comment.

        Returns:
            Review: The updated review with status reset to PENDING.

        Raises:
            HTTPException: If the review is not found or user is not the author.
        """
        review = await self.get_review(review_id, user_id)

        review_data = data.model_dump(exclude_unset=True)
        for key, value in review_data.items():
            setattr(review, key, value)

        # Mark review as unapproved after update
        review.status = ReviewStatus.PENDING
        review.moderated_at = None
        review.moderated_by = None

        return await self.uow.reviews.update(review)

    async def delete_review(self, review_id: UUID, user_id: UUID) -> None:
        """Delete a review.

        Args:
            review_id (UUID): The ID of the review to delete.
            user_id (UUID): The ID of the current user.

        Raises:
            HTTPException: If the review is not found.
        """
        review = await self.get_review(review_id, user_id)
        await self.uow.reviews.delete(review)
