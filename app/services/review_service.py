"""Service for handling review-related operations."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import HTTPException

from app.interfaces.unit_of_work import UnitOfWork
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewRead, ReviewUpdate


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
        self, product_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[ReviewRead]:
        """Get reviews for a specific product.

        Args:
            product_id (UUID): The ID of the product.
            skip (int, optional): Number of reviews to skip. Defaults to 0.
            limit (int, optional): Maximum number of reviews to return. Defaults to 100.

        Returns:
            list[ReviewRead]: List of reviews for the product.

        Raises:
            HTTPException: If the product does not exist.
        """
        product = await self.uow.products.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        return await self.uow.reviews.get_by_product_id(product_id, skip=skip, limit=limit)

    async def get_review(self, review_id: UUID) -> ReviewRead:
        """Get a review by its ID.

        Args:
            review_id (UUID): The ID of the review.

        Returns:
            ReviewRead: The review with the specified ID.

        Raises:
            HTTPException: If the review is not found
        """
        review = await self.uow.reviews.get_by_id(review_id)
        if not review:
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
            HTTPException: If the review is not found
        """
        review = await self.uow.reviews.get_by_id_and_user_id(review_id, user_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

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
