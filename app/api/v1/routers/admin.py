"""Admin dashboard and management API routes for statistics, users, orders, reviews, and inventory."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.v1.dependencies import AdminRoleDep, AdminServiceDep, CurrentUserDep
from app.models.order import OrderStatus
from app.models.review import ReviewStatus
from app.models.user import UserRole
from app.schemas.common import Page
from app.schemas.order import OrderAdminRead, OrderAdminStatusUpdate
from app.schemas.product import ProductRead
from app.schemas.review import ReviewAdminRead
from app.schemas.statistics import (
    AdminDashboard,
    ProductStatistics,
    ReviewStatistics,
    SalesStatistics,
    UserStatistics,
)
from app.schemas.user import UserAdminRead, UserAdminRoleUpdate
from app.utils.pagination import build_page

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[AdminRoleDep])


# ------------------------- Dashboard Overview ------------------------ #
@router.get(
    "/dashboard",
    response_model=AdminDashboard,
    summary="Get dashboard overview",
    description="Retrieve comprehensive admin dashboard with sales, user, product, and review statistics in one request.",
)
async def get_dashboard(
    admin_service: AdminServiceDep,
) -> AdminDashboard:
    """Get complete admin dashboard overview with all statistics."""
    return await admin_service.get_dashboard_data()


# ------------------------ Statistics Endpoints ------------------------ #
@router.get(
    "/statistics/sales",
    response_model=SalesStatistics,
    summary="Get sales statistics",
    description="Retrieve detailed sales metrics including total revenue, order counts, and trends over time.",
)
async def get_sales_statistics(
    admin_service: AdminServiceDep,
) -> SalesStatistics:
    """Get sales statistics."""
    return await admin_service.get_sales_statistics()


@router.get(
    "/statistics/users",
    response_model=UserStatistics,
    summary="Get user statistics",
    description="Retrieve user metrics including total registrations, growth rates, and active user statistics.",
)
async def get_user_statistics(
    admin_service: AdminServiceDep,
) -> UserStatistics:
    """Get user statistics."""
    return await admin_service.get_user_statistics()


@router.get(
    "/statistics/products",
    response_model=ProductStatistics,
    summary="Get product statistics",
    description="Retrieve product metrics including inventory levels, stock status, and catalog statistics.",
)
async def get_product_statistics(
    admin_service: AdminServiceDep,
) -> ProductStatistics:
    """Get product statistics."""
    return await admin_service.get_product_statistics()


@router.get(
    "/statistics/reviews",
    response_model=ReviewStatistics,
    summary="Get review statistics",
    description="Retrieve review metrics including approval rates, average ratings, and pending review counts.",
)
async def get_review_statistics(
    admin_service: AdminServiceDep,
) -> ReviewStatistics:
    """Get review statistics."""
    return await admin_service.get_review_statistics()


# ------------------------ User management ------------------------ #
@router.get(
    "/users",
    response_model=Page[UserAdminRead],
    summary="List users",
    description="Retrieve paginated list of all users with optional filtering by name, email, or role.",
)
async def list_all_users(
    admin_service: AdminServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by name or email"),
    role: Annotated[
        UserRole | None, Query(description="Filter by role: 'customer' or 'admin'")
    ] = None,
) -> Page[UserAdminRead]:
    """List all users with pagination and filters."""
    return await admin_service.get_all_users(
        page=page, page_size=page_size, search=search, role=role
    )


@router.patch(
    "/users/{user_id}/role",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update user role",
    description="Change a user's role between 'customer' and 'admin'. Use with caution as this affects user permissions.",
)
async def update_user_role(
    user_id: UUID,
    role_update: UserAdminRoleUpdate,
    admin_service: AdminServiceDep,
) -> None:
    """Update a user's role."""
    await admin_service.update_user_role(user_id=user_id, new_role=role_update.role)


# ------------------------ Order management ------------------------ #
@router.get(
    "/orders",
    response_model=Page[OrderAdminRead],
    summary="List orders",
    description="Retrieve paginated list of all orders with optional filtering by status or user.",
)
async def list_all_orders(
    admin_service: AdminServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Annotated[OrderStatus | None, Query(description="Filter by order status")] = None,
    user_id: Annotated[UUID | None, Query(description="Filter by user ID")] = None,
) -> Page[OrderAdminRead]:
    """List all orders with pagination and filters."""
    return await admin_service.get_all_orders(
        page=page, page_size=page_size, status=status, user_id=user_id
    )


@router.patch(
    "/orders/{order_id}/status",
    summary="Update order status",
    description="Update the status of an order (e.g., from 'pending' to 'processing', 'shipped', or 'delivered').",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_order_status(
    order_id: UUID,
    status_update: OrderAdminStatusUpdate,
    admin_service: AdminServiceDep,
) -> None:
    """Update an order's status."""
    await admin_service.update_order_status(order_id=order_id, new_status=status_update.status)


# -------------------------- Review management ------------------------ #
@router.get(
    "/reviews",
    response_model=Page[ReviewAdminRead],
    summary="List reviews",
    description="Retrieve paginated list of all reviews with optional filtering by status, user, product, or rating.",
)
async def get_reviews(
    admin_service: AdminServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Annotated[ReviewStatus | None, Query(description="Filter by review status")] = None,
    user_id: Annotated[UUID | None, Query(description="Filter by user ID")] = None,
    product_id: Annotated[UUID | None, Query(description="Filter by product ID")] = None,
    rating: int | None = Query(None, ge=1, le=5, description="Filter by rating"),
) -> Page[ReviewAdminRead]:
    """Get all reviews."""
    total, reviews = await admin_service.get_reviews(
        page=page,
        page_size=page_size,
        status=status,
        product_id=product_id,
        user_id=user_id,
        rating=rating,
    )
    # Manually construct DTOs with relationship data
    review_items = [
        ReviewAdminRead(
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


@router.post(
    "/reviews/{review_id}/approve",
    response_model=ReviewAdminRead,
    summary="Approve review",
    description="Approve a pending review to make it publicly visible on the product page.",
)
async def approve_review(
    review_id: UUID,
    admin_service: AdminServiceDep,
    current_user: CurrentUserDep,
) -> ReviewAdminRead:
    """Approve a review."""
    review = await admin_service.approve_review(review_id=review_id, moderator_id=current_user.id)
    return ReviewAdminRead(
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


@router.patch(
    "/reviews/{review_id}",
    response_model=ReviewAdminRead,
    summary="Reject a review",
    description="Reject a review, marking it as inappropriate or not meeting guidelines.",
)
async def reject_review(
    review_id: UUID,
    admin_service: AdminServiceDep,
    current_user: CurrentUserDep,
) -> ReviewAdminRead:
    """Reject a review."""
    review = await admin_service.reject_review(review_id=review_id, moderator_id=current_user.id)
    return ReviewAdminRead(
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
    "/inventory/low-stock",
    response_model=list[ProductRead],
    summary="Get low stock products",
    description="Retrieve products with stock levels below the specified threshold for inventory monitoring and restocking alerts.",
)
async def get_low_stock_products(
    admin_service: AdminServiceDep,
    threshold: int = Query(10, ge=1, description="Stock threshold for alerts"),
) -> list[ProductRead]:
    """Get low stock product alerts."""
    return await admin_service.get_low_stock_products(threshold=threshold)


@router.get(
    "/inventory/top-moving",
    response_model=list[ProductRead],
    summary="Get top-moving products",
    description="Retrieve the best-selling products ranked by order volume. Useful for identifying popular items and inventory planning.",
)
async def get_top_moving_products(
    admin_service: AdminServiceDep,
    limit: int = Query(10, ge=1, description="Number of top products to retrieve"),
) -> list[ProductRead]:
    """Get top-moving products."""
    return await admin_service.get_top_selling_products(limit=limit)
