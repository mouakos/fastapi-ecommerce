"""Product review API routes for creating, updating, and moderating customer reviews."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.v1.dependencies import CurrentUserDep, ReviewServiceDep
from app.schemas.common import Page
from app.schemas.review import ReviewCreate, ReviewRead, ReviewUpdate
from app.utils.pagination import build_page

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
    response_model=Page[ReviewRead],
    summary="Get product reviews",
    description="Retrieve all approved reviews for a specific product with pagination support.",
)
async def get_product_reviews(
    product_id: UUID,
    review_service: ReviewServiceDep,
    page: int = Query(1, description="Page number"),
    page_size: int = Query(10, description="Number of reviews per page"),
) -> Page[ReviewRead]:
    """Get all reviews for a specific product."""
    total, items = await review_service.get_product_reviews(
        product_id, page=page, page_size=page_size
    )
    return build_page(items=items, page=page, size=page_size, total=total)  # type: ignore [arg-type]


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
