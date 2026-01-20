"""Product review API routes for creating, updating, and moderating customer reviews."""

# mypy: disable-error-code=return-value
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.v1.dependencies import CurrentUserDep, ReviewServiceDep
from app.schemas.common import Page, SortOrder
from app.schemas.review import ReviewCreate, ReviewRead, ReviewSortByField, ReviewUpdate
from app.utils.pagination import build_page

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post(
    "",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create product review",
    description="Submit a new review with rating (1-5 stars) and optional comment for a product. Review status will be PENDING until approved by an administrator.",
)
async def create_review(
    data: ReviewCreate,
    review_service: ReviewServiceDep,
    current_user: CurrentUserDep,
) -> ReviewRead:
    """Create a new review for a product."""
    return await review_service.create_review(current_user.id, data)


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
    rating: int | None = Query(None, ge=1, le=5, description="Filter reviews by rating"),
    sort_by: Annotated[
        ReviewSortByField, Query(description="Field to sort by")
    ] = ReviewSortByField.CREATED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort order")] = SortOrder.DESC,
) -> Page[ReviewRead]:
    """Get all reviews for a specific product."""
    total, items = await review_service.get_product_reviews(
        product_id=product_id,
        page=page,
        page_size=page_size,
        rating=rating,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
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
    current_user: CurrentUserDep,
) -> ReviewRead:
    """Get a review by its ID."""
    return await review_service.get_review(review_id, current_user.id)


@router.patch(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Update review",
    description="Update an existing review's rating or comment. Only the review author can modify their own review.",
)
async def update_review(
    review_id: UUID,
    data: ReviewUpdate,
    review_service: ReviewServiceDep,
    current_user: CurrentUserDep,
) -> ReviewRead:
    """Update a review by its ID."""
    return await review_service.update_review(review_id, current_user.id, data)


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete review",
    description="Permanently delete a review. Only the review author can delete their own review. This action cannot be undone.",
)
async def delete_review(
    review_id: UUID,
    review_service: ReviewServiceDep,
    current_user: CurrentUserDep,
) -> None:
    """Delete a review by its ID."""
    await review_service.delete_review(review_id, current_user.id)
