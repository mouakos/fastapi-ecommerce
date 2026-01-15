"""Admin routes for analytics, user management, order management, review moderation, and inventory management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.v1.dependencies import AdminRoleDep, AdminServiceDep
from app.models.order import OrderStatus
from app.models.user import UserRole
from app.schemas.admin_schema import (
    DashboardOverview,
    OrderAdminRead,
    OrderStatusUpdate,
    Paged,
    ProductAnalytics,
    ReviewAdminRead,
    ReviewAnalytics,
    SalesAnalytics,
    UserAdminRead,
    UserAnalytics,
    UserRoleUpdate,
)
from app.schemas.product_schema import ProductRead

admin_router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[AdminRoleDep])


# Dashboard overview
@admin_router.get(
    "/dashboard",
    response_model=DashboardOverview,
    summary="Get dashboard overview",
    description="Retrieve comprehensive admin dashboard with sales, user, product, and review analytics in one request.",
)
async def get_dashboard(
    admin_service: AdminServiceDep,
) -> DashboardOverview:
    """Get complete admin dashboard overview with all analytics."""
    return await admin_service.get_dashboard_data()


# Analytics endpoints
@admin_router.get(
    "/analytics/sales",
    response_model=SalesAnalytics,
    summary="Get sales analytics",
    description="Retrieve detailed sales metrics including total revenue, order counts, and trends over time.",
)
async def get_sales_analytics(
    admin_service: AdminServiceDep,
) -> SalesAnalytics:
    """Get sales analytics."""
    return await admin_service.get_sales_analytics()


@admin_router.get(
    "/analytics/users",
    response_model=UserAnalytics,
    summary="Get user analytics",
    description="Retrieve user metrics including total registrations, growth rates, and active user statistics.",
)
async def get_user_analytics(
    admin_service: AdminServiceDep,
) -> UserAnalytics:
    """Get user analytics."""
    return await admin_service.get_user_analytics()


@admin_router.get(
    "/analytics/products",
    response_model=ProductAnalytics,
    summary="Get product analytics",
    description="Retrieve product metrics including inventory levels, stock status, and catalog statistics.",
)
async def get_product_analytics(
    admin_service: AdminServiceDep,
) -> ProductAnalytics:
    """Get product analytics."""
    return await admin_service.get_product_analytics()


@admin_router.get(
    "/analytics/reviews",
    response_model=ReviewAnalytics,
    summary="Get review analytics",
    description="Retrieve review metrics including approval rates, average ratings, and pending review counts.",
)
async def get_review_analytics(
    admin_service: AdminServiceDep,
) -> ReviewAnalytics:
    """Get review analytics."""
    return await admin_service.get_review_analytics()


# User management
@admin_router.get(
    "/users",
    response_model=Paged[UserAdminRead],
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
) -> Paged[UserAdminRead]:
    """List all users with pagination and filters."""
    return await admin_service.get_all_users(
        page=page, page_size=page_size, search=search, role=role
    )


@admin_router.patch(
    "/users/{user_id}/role",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update user role",
    description="Change a user's role between 'customer' and 'admin'. Use with caution as this affects user permissions.",
)
async def update_user_role(
    user_id: UUID,
    role_update: UserRoleUpdate,
    admin_service: AdminServiceDep,
) -> None:
    """Update a user's role."""
    await admin_service.update_user_role(user_id=user_id, new_role=role_update.role)


# Order management
@admin_router.get(
    "/orders",
    response_model=Paged[OrderAdminRead],
    summary="List orders",
    description="Retrieve paginated list of all orders with optional filtering by status or user.",
)
async def list_all_orders(
    admin_service: AdminServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Annotated[OrderStatus | None, Query(description="Filter by order status")] = None,
    user_id: Annotated[UUID | None, Query(description="Filter by user ID")] = None,
) -> Paged[OrderAdminRead]:
    """List all orders with pagination and filters."""
    return await admin_service.get_all_orders(
        page=page, page_size=page_size, status=status, user_id=user_id
    )


@admin_router.patch(
    "/orders/{order_id}/status",
    summary="Update order status",
    description="Update the status of an order (e.g., from 'pending' to 'processing', 'shipped', or 'delivered').",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_order_status(
    order_id: UUID,
    status_update: OrderStatusUpdate,
    admin_service: AdminServiceDep,
) -> None:
    """Update an order's status."""
    await admin_service.update_order_status(order_id=order_id, new_status=status_update.status)


# Review moderation
@admin_router.get(
    "/reviews",
    response_model=Paged[ReviewAdminRead],
    summary="List reviews",
    description="Retrieve paginated list of all reviews with optional filtering by approval status.",
)
async def get_all_reviews(
    admin_service: AdminServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    is_approved: Annotated[bool | None, Query(description="Filter by approval status")] = None,
) -> Paged[ReviewAdminRead]:
    """Get all reviews."""
    return await admin_service.get_all_reviews(
        page=page, page_size=page_size, is_approved=is_approved
    )


@admin_router.post(
    "/reviews/{review_id}/approve",
    summary="Approve review",
    description="Approve a pending review to make it publicly visible on the product page.",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def approve_review(
    review_id: UUID,
    admin_service: AdminServiceDep,
) -> None:
    """Approve a review."""
    await admin_service.approve_review(review_id=review_id)


@admin_router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reject and delete review",
    description="Permanently reject and delete a review. This action cannot be undone.",
)
async def reject_review(
    review_id: UUID,
    admin_service: AdminServiceDep,
) -> None:
    """Reject/delete a review."""
    await admin_service.reject_review(review_id=review_id)


# Inventory management
@admin_router.get(
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


@admin_router.get(
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
