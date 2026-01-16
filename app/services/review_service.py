"""Service for handling review-related operations."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import HTTPException

from app.interfaces.unit_of_work import UnitOfWork
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewRead, ReviewUpdate


# TODO: return only approved reviews in get_product_review and get_review methods
class ReviewService:
    """Service for handling review-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def add_product_review(self, user_id: UUID, data: ReviewCreate) -> ReviewRead:
        """Create a new review for a product.

        Args:
            user_id (UUID): The ID of the user creating the review.
            data (ReviewCreate): Data for the new review.

        Returns:
            ReviewRead: The created review.

        Raises:
            HTTPException: Product does not exist or user has already reviewed the product or
                has not purchased the product.
        """
        product = await self.uow.products.get_by_id(data.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        existing = await self.uow.reviews.get_by_user_id_and_product_id(user_id, data.product_id)
        if existing:
            raise HTTPException(status_code=400, detail="You have already reviewed this product.")

        # TODO: Verify if the user has purchased the product before allowing review
        purchased = await self.uow.orders.user_has_purchased_product(user_id, data.product_id)
        if not purchased:
            raise HTTPException(
                status_code=400, detail="You can only review products you have purchased."
            )

        review_data = data.model_dump()
        new_review = Review(
            user_id=user_id,
            **review_data,
        )
        return await self.uow.reviews.add(new_review)

    async def get_product_reviews(
        self, product_id: UUID, page: int = 1, page_size: int = 10
    ) -> list[ReviewRead]:
        """Get reviews for a specific product.

        Args:
            product_id (UUID): The ID of the product.
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of reviews per page. Defaults to 10.

        Returns:
            list[ReviewRead]: List of reviews for the product.

        Raises:
            HTTPException: If the product does not exist.
        """
        product = await self.uow.products.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        _, reviews = await self.uow.reviews.get_all_paginated(
            page=page, page_size=page_size, is_approved=True
        )
        return reviews

    async def get_review(self, review_id: UUID) -> ReviewRead:
        """Get a review by its ID.

        Args:
            review_id (UUID): The ID of the review.

        Returns:
            ReviewRead: The review with the specified ID.

        Raises:
            HTTPException: If the review is not found or not approved.
        """
        review = await self.uow.reviews.get_by_id(review_id)
        if not review or not review.is_approved:
            raise HTTPException(status_code=404, detail="Review not found.")

        return review

    async def update_review(self, review_id: UUID, user_id: UUID, data: ReviewUpdate) -> ReviewRead:
        """Update a review by its ID.

        Args:
            review_id (UUID): The ID of the review to update.
            user_id (UUID): The ID of the current user.
            data (ReviewUpdate): Updated data for the review.

        Returns:
            ReviewRead: The updated review.

        Raises:
            HTTPException: If the review is not found or if the review is approved and cannot be modified.
        """
        review = await self.uow.reviews.get_by_id_and_user_id(review_id, user_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

        # TODO: Prevent updates to approved reviews
        if review.is_approved:
            raise HTTPException(status_code=400, detail="Approved reviews cannot be modified.")

        review_data = data.model_dump(exclude_unset=True)
        for key, value in review_data.items():
            setattr(review, key, value)

        return await self.uow.reviews.update(review)

    async def delete_review(self, review_id: UUID, user_id: UUID) -> None:
        """Delete a review by its ID.

        Args:
            review_id (UUID): The ID of the review to delete.
            user_id (UUID): The ID of the current user.
        """
        review = await self.uow.reviews.get_by_id_and_user_id(review_id, user_id)

        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

        await self.uow.reviews.delete_by_id(review_id)
