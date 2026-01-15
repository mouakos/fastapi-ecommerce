"""Schemas for admin dashboard and management operations."""

from ast import TypeVar
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus
from app.models.payment import PaymentStatus
from app.models.user import UserRole
from app.schemas.common import UUIDMixin


class SalesAnalytics(BaseModel):
    """Schema for sales analytics data."""

    total_revenue: Decimal = Field(..., description="Total revenue from all orders")
    total_orders: int = Field(..., description="Total number of orders")
    pending_orders: int = Field(..., description="Orders with pending status")
    paid_orders: int = Field(..., description="Orders with paid status")
    shipped_orders: int = Field(..., description="Orders with shipped status")
    delivered_orders: int = Field(..., description="Orders with delivered status")
    cancelled_orders: int = Field(..., description="Orders with cancelled status")
    average_order_value: Decimal = Field(
        ..., description="Average order value", ge=0, decimal_places=2, max_digits=10
    )
    revenue_last_30_days: Decimal = Field(
        ..., description="Revenue from last 30 days", ge=0, decimal_places=2, max_digits=10
    )


class UserAnalytics(BaseModel):
    """Schema for user analytics data."""

    total_users: int = Field(..., description="Total number of users")
    total_customers: int = Field(..., description="Number of customer users")
    total_admins: int = Field(..., description="Number of admin users")
    new_users_last_30_days: int = Field(..., description="New users in last 30 days")


class ProductAnalytics(BaseModel):
    """Schema for product analytics data."""

    total_products: int = Field(..., description="Total number of products")
    active_products: int = Field(..., description="Number of active products")
    inactive_products: int = Field(..., description="Number of inactive products")
    out_of_stock_count: int = Field(..., description="Number of out of stock products")
    low_stock_count: int = Field(..., description="Number of low stock products (< 10)")


class ReviewAnalytics(BaseModel):
    """Schema for review analytics data."""

    total_reviews: int = Field(..., description="Total number of reviews")
    pending_reviews: int = Field(..., description="Reviews awaiting approval")
    approved_reviews: int = Field(..., description="Approved reviews")
    average_rating: float | None = Field(None, description="Average rating across all reviews")


class DashboardOverview(BaseModel):
    """Schema for comprehensive dashboard overview data."""

    sales: SalesAnalytics
    users: UserAnalytics
    products: ProductAnalytics
    reviews: ReviewAnalytics


T = TypeVar("T")


class Paged[T](BaseModel):
    """Pagination information."""

    items: list[T]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(frozen=True)


class UserAdminRead(UUIDMixin):
    """Schema for reading user information in admin context."""

    email: str
    first_name: str | None
    last_name: str | None
    role: UserRole
    created_at: datetime
    updated_at: datetime
    is_superuser: bool
    total_orders: int = Field(..., description="Total orders by this user")
    total_spent: Decimal = Field(
        ..., description="Total amount spent by this user", ge=0, decimal_places=2, max_digits=10
    )

    model_config = ConfigDict(frozen=True)


class UserRoleUpdate(BaseModel):
    """Schema for updating a user's role."""

    role: UserRole = Field(..., description="New role: 'user' or 'admin'")

    model_config = ConfigDict(frozen=True)


class OrderAdminRead(UUIDMixin):
    """Schema for reading order information in admin context."""

    order_number: str
    user_id: UUID
    user_email: str = Field(..., description="Email of the user who placed the order")
    total_amount: Decimal
    status: str
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    shipped_at: datetime | None
    paid_at: datetime | None
    canceled_at: datetime | None
    delivered_at: datetime | None

    model_config = ConfigDict(frozen=True)


class OrderStatusUpdate(BaseModel):
    """Schema for updating an order's status."""

    status: OrderStatus = Field(
        ...,
        description="New status: 'pending', 'paid', 'shipped', 'delivered', 'cancelled'",
    )

    model_config = ConfigDict(frozen=True)


class ReviewAdminRead(UUIDMixin):
    """Schema for reading review information in admin context."""

    user_id: UUID
    user_email: str
    product_id: UUID
    product_name: str
    rating: int
    comment: str | None
    created_at: datetime
    updated_at: datetime
    is_approved: bool

    model_config = ConfigDict(frozen=True)
