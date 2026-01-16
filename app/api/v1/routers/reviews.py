"""Product review API routes for creating, updating, and moderating customer reviews."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.v1.dependencies import CurrentUserDep, ReviewServiceDep
from app.schemas.review import ReviewCreate, ReviewRead, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post(
    "",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add product review",
    description="Submit a new review for a product with rating and optional comment. Requires authentication.",
)
async def add_product_review(
    data: ReviewCreate,
    review_service: ReviewServiceDep,
    current_user: CurrentUserDep,
) -> ReviewRead:
    """Create a new review for a product."""
    return await review_service.add_product_review(current_user.id, data)


@router.get(
    "/product/{product_id}",
    response_model=list[ReviewRead],
    summary="Get product reviews",
    description="Retrieve all approved reviews for a specific product with pagination support.",
)
async def get_product_reviews(
    product_id: UUID,
    review_service: ReviewServiceDep,
    skip: int = Query(0, description="Number of reviews to skip"),
    limit: int = Query(100, description="Maximum number of reviews to return"),
) -> list[ReviewRead]:
    """Get all reviews for a specific product."""
    return await review_service.get_product_reviews(product_id, skip=skip, limit=limit)


@router.get(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Get review by ID",
    description="Retrieve detailed information about a specific review using its UUID.",
)
async def get_review(
    review_id: UUID,
    review_service: ReviewServiceDep,
) -> ReviewRead:
    """Get a review by its ID."""
    return await review_service.get_review(review_id)


@router.patch(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Update review",
    description="Update an existing review's rating or comment. Only the review author can modify their review.",
)
async def update_review(
    review_id: UUID,
    data: ReviewUpdate,
    review_service: ReviewServiceDep,
    current_user: CurrentUserDep,
) -> ReviewRead:
    """Update a review by its ID."""
    return await review_service.update_review(current_user.id, review_id, data)


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete review",
    description="Permanently delete a review. Only the review author can delete their review. This action cannot be undone.",
)
async def delete_review(
    review_id: UUID,
    review_service: ReviewServiceDep,
    current_user: CurrentUserDep,
) -> None:
    """Delete a review by its ID."""
    await review_service.delete_review(current_user.id, review_id)
