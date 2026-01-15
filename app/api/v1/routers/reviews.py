"""Review API routes."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.v1.dependencies import CurrentUserDep, ReviewServiceDep
from app.schemas.review_schema import ReviewCreate, ReviewRead, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post(
    "/",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new review for a product",
)
async def create_review(
    data: ReviewCreate,
    review_service: ReviewServiceDep,
    current_user: CurrentUserDep,
) -> ReviewRead:
    """Create a new review for a product."""
    return await review_service.create(current_user.id, data)


@router.get(
    "/product/{product_id}",
    response_model=list[ReviewRead],
    summary="Get all reviews for a specific product",
)
async def get_reviews_by_product(
    product_id: UUID,
    review_service: ReviewServiceDep,
    skip: int = Query(0, description="Number of reviews to skip"),
    limit: int = Query(100, description="Maximum number of reviews to return"),
) -> list[ReviewRead]:
    """Get all reviews for a specific product."""
    return await review_service.get_by_product(product_id, skip=skip, limit=limit)


@router.get(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Get a review by its ID",
)
async def get_review_by_id(
    review_id: UUID,
    review_service: ReviewServiceDep,
) -> ReviewRead:
    """Get a review by its ID."""
    return await review_service.get_by_id(review_id)


@router.patch(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Update a review by its ID",
)
async def update_review(
    review_id: UUID,
    data: ReviewUpdate,
    review_service: ReviewServiceDep,
    current_user: CurrentUserDep,
) -> ReviewRead:
    """Update a review by its ID. Only the review author can update their review."""
    return await review_service.update(current_user.id, review_id, data)


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a review by its ID",
)
async def delete_review(
    review_id: UUID,
    review_service: ReviewServiceDep,
    current_user: CurrentUserDep,
) -> None:
    """Delete a review by its ID. Only the review author or an admin can delete a review."""
    await review_service.delete(current_user.id, review_id)
