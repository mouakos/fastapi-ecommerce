"""Admin dashboard and management API routes for statistics, users, orders, reviews, and inventory."""

# mypy: disable-error-code=return-value
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.cache import cache
from app.api.v1.dependencies import AdminRoleDep, AdminServiceDep, CurrentUserDep
from app.models.order import OrderStatus
from app.models.review import ReviewStatus
from app.models.user import UserRole
from app.schemas.analytics import (
    AdminDashboard,
    ProductAnalytics,
    ReviewAnalytics,
    SalesAnalytics,
    UserAnalytics,
)
from app.schemas.common import Page, SortOrder
from app.schemas.order import (
    OrderActionResponse,
    OrderAdmin,
    OrderSortByField,
)
from app.schemas.product import (
    ProductAdmin,
    ProductAvailabilityFilter,
    ProductPublic,
    ProductSortByField,
)
from app.schemas.review import ReviewActionResponse, ReviewAdmin, ReviewSortByField
from app.schemas.user import UserActionResponse, UserAdmin, UserRoleUpdateRequest, UserSortByField
from app.utils.pagination import build_page

router = APIRouter(dependencies=[AdminRoleDep])


# ------------------------- Dashboard Overview ------------------------ #
@router.get(
    "/dashboard",
    response_model=AdminDashboard,
    summary="Get dashboard overview",
    description="Retrieve comprehensive admin dashboard with sales, user, product, and review statistics in one request.",
)
@cache(expire=30)
async def get_dashboard(
    admin_service: AdminServiceDep,
) -> AdminDashboard:
    """Get complete admin dashboard overview with all statistics."""
    return await admin_service.get_dashboard_data()


# ------------------------ Statistics Endpoints ------------------------ #
@router.get(
    "/analytics/sales",
    response_model=SalesAnalytics,
    summary="Get sales analytics",
    description="Retrieve detailed sales metrics including total revenue, order counts, and trends over time.",
)
@cache(expire=30)
async def get_sales_analytics(
    admin_service: AdminServiceDep,
) -> SalesAnalytics:
    """Get sales analytics."""
    return await admin_service.get_sales_analytics()


@router.get(
    "/analytics/users",
    response_model=UserAnalytics,
    summary="Get user analytics",
    description="Retrieve user metrics including total registrations, growth rates, and active user statistics.",
)
@cache(expire=60)
async def get_user_analytics(
    admin_service: AdminServiceDep,
) -> UserAnalytics:
    """Get user analytics."""
    return await admin_service.get_user_analytics()


@router.get(
    "/analytics/products",
    response_model=ProductAnalytics,
    summary="Get product analytics",
    description="Retrieve product metrics including inventory levels, stock status, and catalog analytics.",
)
@cache(expire=60)
async def get_product_analytics(
    admin_service: AdminServiceDep,
) -> ProductAnalytics:
    """Get product analytics."""
    return await admin_service.get_product_analytics()


@router.get(
    "/analytics/reviews",
    response_model=ReviewAnalytics,
    summary="Get review analytics",
    description="Retrieve review metrics including approval rates, average ratings, and pending review counts.",
)
@cache(expire=60)
async def get_review_analytics(
    admin_service: AdminServiceDep,
) -> ReviewAnalytics:
    """Get review analytics."""
    return await admin_service.get_review_analytics()


# ------------------------ User management ------------------------ #
@router.get(
    "/users",
    response_model=Page[UserAdmin],
    summary="Get all users",
    description="Retrieve paginated list of all users with optional filtering by name, email, or role.",
)
@cache(expire=10)
async def get_users(
    admin_service: AdminServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by last name, first name or email"),
    role: Annotated[
        UserRole | None, Query(description="Filter by role: 'customer' or 'admin'")
    ] = None,
    sort_by: Annotated[
        UserSortByField,
        Query(description="Field to sort by"),
    ] = UserSortByField.CREATED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort order")] = SortOrder.DESC,
) -> Page[UserAdmin]:
    """Get all users with optional filters, sorting, and pagination."""
    users, total = await admin_service.get_users(
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
    )
    users_dto = [
        UserAdmin(
            id=user.id,
            email=user.email,
            is_superuser=user.is_superuser,
            role=user.role,
            first_name=user.first_name,
            last_name=user.last_name,
            phone_number=user.phone_number,
            created_at=user.created_at,
            updated_at=user.updated_at,
            total_orders=await admin_service.count_user_orders(user.id),
            total_spent=await admin_service.get_user_total_spent(user.id),
        )
        for user in users
    ]

    return build_page(total=total, items=users_dto, page=page, size=page_size)


@router.patch(
    "/users/{user_id}/role",
    summary="Update user role",
    description="Change a user's role between 'customer' and 'admin'. Use with caution as this affects user permissions.",
)
async def update_user_role(
    user_id: UUID,
    role_update: UserRoleUpdateRequest,
    admin_service: AdminServiceDep,
    current_user: CurrentUserDep,
) -> UserActionResponse:
    """Update a user's role."""
    await admin_service.update_user_role(
        current_user_id=current_user.id, user_id=user_id, new_role=role_update.role
    )
    return UserActionResponse(message="User role updated successfully.", user_id=user_id)


# ------------------------ Order management ------------------------ #
@router.get(
    "/orders",
    response_model=Page[OrderAdmin],
    summary="List all orders",
    description="Retrieve paginated list of all orders across all users with optional filtering by status and user, plus sorting options.",
)
@cache(expire=10)
async def get_orders(
    admin_service: AdminServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Annotated[OrderStatus | None, Query(description="Filter by order status")] = None,
    user_id: Annotated[UUID | None, Query(description="Filter by user ID")] = None,
    sort_by: Annotated[
        OrderSortByField, Query(description="Field to sort by")
    ] = OrderSortByField.CREATED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort order")] = SortOrder.DESC,
) -> Page[OrderAdmin]:
    """Get all orders with optional filters, sorting, and pagination."""
    orders, total = await admin_service.get_orders(
        page=page,
        page_size=page_size,
        status=status,
        user_id=user_id,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
    )
    orders_dto = [
        OrderAdmin(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            total_amount=order.total_amount,
            created_at=order.created_at,
            updated_at=order.updated_at,
            order_number=order.order_number,
            user_email=order.user.email,
            shipped_at=order.shipped_at,
            delivered_at=order.delivered_at,
            paid_at=order.paid_at,
            canceled_at=order.canceled_at,
        )
        for order in orders
    ]
    return build_page(items=orders_dto, page=page, size=page_size, total=total)


@router.patch(
    "/orders/{order_id}/mark-shipped",
    summary="Mark order as shipped",
    description="Mark an order as shipped, updating its status accordingly.",
)
async def mark_order_as_shipped(
    order_id: UUID,
    admin_service: AdminServiceDep,
) -> OrderActionResponse:
    """Mark an order as shipped."""
    await admin_service.mark_order_as_shipped(order_id=order_id)
    return OrderActionResponse(message="Order status updated to shipped.", order_id=order_id)


# -------------------------- Review management ------------------------ #
@router.get(
    "/reviews",
    response_model=Page[ReviewAdmin],
    summary="List all reviews",
    description="Retrieve paginated list of all reviews across all products and users with optional filtering by status, rating, user, and product. Includes moderation information.",
)
@cache(expire=10)
async def get_reviews(
    admin_service: AdminServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Annotated[ReviewStatus | None, Query(description="Filter by review status")] = None,
    user_id: Annotated[UUID | None, Query(description="Filter by user ID")] = None,
    product_id: Annotated[UUID | None, Query(description="Filter by product ID")] = None,
    rating: int | None = Query(None, ge=1, le=5, description="Filter by rating"),
    sort_by: Annotated[
        ReviewSortByField, Query(description="Field to sort by")
    ] = ReviewSortByField.CREATED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort order")] = SortOrder.DESC,
) -> Page[ReviewAdmin]:
    """Get all reviews with optional filters, sorting, and pagination."""
    reviews, total = await admin_service.get_reviews(
        page=page,
        page_size=page_size,
        status=status,
        product_id=product_id,
        user_id=user_id,
        rating=rating,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
    )
    # Manually construct DTOs with relationship data
    review_items = [
        ReviewAdmin(
            id=review.id,
            rating=review.rating,
            comment=review.comment,
            user_id=review.user_id,
            product_id=review.product_id,
            created_at=review.created_at,
            user_email=review.user.email,
            product_name=review.product.name,
            status=review.status,
            moderated_at=review.moderated_at,
            moderated_by=review.moderated_by,
            updated_at=review.updated_at,
        )
        for review in reviews
    ]
    return build_page(items=review_items, page=page, size=page_size, total=total)


@router.patch(
    "/reviews/{review_id}/approve",
    response_model=ReviewActionResponse,
    summary="Approve review",
    description="Approve a pending review to make it publicly visible on the product page.",
)
async def approve_review(
    review_id: UUID,
    admin_service: AdminServiceDep,
    current_user: CurrentUserDep,
) -> ReviewActionResponse:
    """Approve a review."""
    await admin_service.approve_review(review_id=review_id, moderator_id=current_user.id)
    return ReviewActionResponse(
        message="Review approved successfully.",
        review_id=review_id,
    )


@router.patch(
    "/reviews/{review_id}/reject",
    response_model=ReviewActionResponse,
    summary="Reject review",
    description="Reject a review and prevent it from being displayed publicly. Use for reviews that violate guidelines or are inappropriate.",
)
async def reject_review(
    review_id: UUID,
    admin_service: AdminServiceDep,
    current_user: CurrentUserDep,
) -> ReviewActionResponse:
    """Reject a review."""
    await admin_service.reject_review(review_id=review_id, moderator_id=current_user.id)
    return ReviewActionResponse(
        message="Review rejected successfully.",
        review_id=review_id,
    )


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete review",
    description="Delete a review from the system. This action is irreversible.",
)
async def delete_review(
    review_id: UUID,
    admin_service: AdminServiceDep,
) -> None:
    """Delete a review."""
    await admin_service.delete_review(review_id=review_id)


# ------------------------ Product management ------------------------ #


@router.get(
    "/products",
    response_model=Page[ProductAdmin],
    summary="Get all products",
    description="Retrieve paginated list of all products with optional filtering by stock levels and active status.",
)
@cache(expire=10)
async def get_products(
    admin_service: AdminServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=255,
            description="Search query for product name or description (case-insensitive)",
        ),
    ] = None,
    category_id: Annotated[UUID | None, Query(description="Filter by category ID")] = None,
    category_slug: Annotated[str | None, Query(description="Filter by category slug")] = None,
    min_price: Annotated[Decimal | None, Query(ge=0, description="Minimum price")] = None,
    max_price: Annotated[Decimal | None, Query(ge=0, description="Maximum price")] = None,
    min_rating: Annotated[
        int | None, Query(ge=1, le=5, description="Minimum average rating (1-5)")
    ] = None,
    availability: Annotated[
        ProductAvailabilityFilter, Query(description="Stock availability")
    ] = ProductAvailabilityFilter.ALL,
    is_active: Annotated[
        bool | None, Query(description="Filter by active status: true, false, or omit for all")
    ] = None,
    sort_by: Annotated[
        ProductSortByField, Query(description="Sort by field")
    ] = ProductSortByField.CREATED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort order")] = SortOrder.ASC,
) -> Page[ProductAdmin]:
    """Get all products with optional filters, sorting, and pagination."""
    products, total = await admin_service.get_products(
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        category_slug=category_slug,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        availability=availability,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order.value,
    )
    return build_page(items=products, page=page, size=page_size, total=total)  # type: ignore [arg-type]


@router.get(
    "/products/low-stock",
    response_model=Page[ProductPublic],
    summary="Get low stock products",
    description="Retrieve products with stock levels below the specified threshold for inventory monitoring and restocking alerts.",
)
@cache(expire=30)
async def get_low_stock_products(
    admin_service: AdminServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    threshold: int = Query(10, ge=0, description="Stock threshold for alerts"),
    is_active: Annotated[
        bool | None, Query(description="Filter by active status: true, false, or omit for all")
    ] = None,
) -> Page[ProductPublic]:
    """Get low stock product alerts."""
    products, total = await admin_service.get_low_stock_products(
        threshold=threshold, is_active=is_active, page=page, page_size=page_size
    )
    return build_page(items=products, page=page, size=page_size, total=total)  # type: ignore [arg-type]


@router.get(
    "/products/top-moving",
    response_model=list[ProductPublic],
    summary="Get top-moving products",
    description="Retrieve top-selling products within a specified time frame to identify bestsellers and trends.",
)
@cache(expire=60)
async def get_top_moving_products(
    admin_service: AdminServiceDep,
    limit: int = Query(10, ge=1, description="Number of top products to retrieve"),
    days: int = Query(30, ge=1, le=365, description="Time frame in days to consider for top sales"),
) -> list[ProductPublic]:
    """Get top-moving products."""
    return await admin_service.get_top_selling_products(limit=limit, days=days)
