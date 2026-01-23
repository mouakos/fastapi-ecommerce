"""Schemas for statistics data."""

from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import TwoDecimalBaseModel


class SalesAnalytics(TwoDecimalBaseModel):
    """Schema for sales analytics data."""

    total_revenue: Decimal = Field(..., description="Total revenue from all orders")
    total_orders: int = Field(..., description="Total number of orders")
    pending_orders: int = Field(..., description="Orders with pending status")
    paid_orders: int = Field(..., description="Orders with paid status")
    shipped_orders: int = Field(..., description="Orders with shipped status")
    delivered_orders: int = Field(..., description="Orders with delivered status")
    cancelled_orders: int = Field(..., description="Orders with cancelled status")
    average_order_value: Decimal = Field(
        ..., description="Average order value", ge=0, max_digits=10
    )
    revenue_last_30_days: Decimal = Field(
        ..., description="Revenue from last 30 days", ge=0, max_digits=10
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


class AdminDashboard(BaseModel):
    """Schema for admin dashboard analytics."""

    sales: SalesAnalytics
    users: UserAnalytics
    products: ProductAnalytics
    reviews: ReviewAnalytics
