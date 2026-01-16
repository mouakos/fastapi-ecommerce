"""Service layer for admin-related operations."""

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException

from app.interfaces.unit_of_work import UnitOfWork
from app.models.order import OrderStatus
from app.models.user import UserRole
from app.schemas.admin import (
    DashboardOverview,
    OrderAdminRead,
    Paged,
    ProductAnalytics,
    ReviewAdminRead,
    ReviewAnalytics,
    SalesAnalytics,
    UserAdminRead,
    UserAnalytics,
)
from app.schemas.product import ProductRead
from app.utils.utc_time import utcnow


class AdminService:
    """Service class for admin-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    _ALLOWED_ORDER_STATUS_TRANSITIONS = {
        OrderStatus.PENDING: {OrderStatus.PAID, OrderStatus.CANCELED},
        OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELED},
        OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
        OrderStatus.DELIVERED: set(),
        OrderStatus.CANCELED: set(),
    }

    async def get_sales_analytics(self) -> SalesAnalytics:
        """Retrieve sales analytics data.

        Returns:
            SalesAnalytics: Sales analytics data.
        """
        # Total orders and revenue
        total_orders = await self.uow.orders.count_all()
        total_revenue = await self.uow.orders.get_total_sales()

        # Orders by status
        pending_orders = await self.uow.orders.count_all(status=OrderStatus.PENDING)
        paid_orders = await self.uow.orders.count_all(status=OrderStatus.PAID)
        shipped_orders = await self.uow.orders.count_all(status=OrderStatus.SHIPPED)
        delivered_orders = await self.uow.orders.count_all(status=OrderStatus.DELIVERED)
        cancelled_orders = await self.uow.orders.count_all(status=OrderStatus.CANCELED)

        # Average order value
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0.0

        # Revenue in the last 30 days
        revenue_last_30_days = await self.uow.orders.get_total_sales_by_last_days(days=30)

        return SalesAnalytics(
            total_revenue=total_revenue,
            total_orders=total_orders,
            pending_orders=pending_orders,
            paid_orders=paid_orders,
            shipped_orders=shipped_orders,
            delivered_orders=delivered_orders,
            cancelled_orders=cancelled_orders,
            average_order_value=Decimal(str(average_order_value)),
            revenue_last_30_days=revenue_last_30_days,
        )

    async def get_user_analytics(self) -> UserAnalytics:
        """Retrieve user analytics data.

        Returns:
            UserAnalytics: User analytics data.
        """
        total_users = await self.uow.users.count_all()
        total_customers = await self.uow.users.count_all(role=UserRole.USER)
        total_admins = await self.uow.users.count_all(role=UserRole.ADMIN)

        # New users in the last 30 days
        new_users_last_30_days = await self.uow.users.count_recent_users(days=30)

        return UserAnalytics(
            total_users=total_users,
            total_customers=total_customers,
            total_admins=total_admins,
            new_users_last_30_days=new_users_last_30_days,
        )

    async def get_product_analytics(self) -> ProductAnalytics:
        """Retrieve product analytics data.

        Returns:
            ProductAnalytics: Product analytics data.
        """
        total_products = await self.uow.products.count_all()
        active_products = await self.uow.products.count_all(is_active=True)
        inactive_products = await self.uow.products.count_all(is_active=False)
        out_of_stock_count = await self.uow.products.count_all(stock=0)
        low_stock_count = await self.uow.products.count_low_stock(threshold=10)

        return ProductAnalytics(
            total_products=total_products,
            active_products=active_products,
            inactive_products=inactive_products,
            out_of_stock_count=out_of_stock_count,
            low_stock_count=low_stock_count,
        )

    async def get_review_analytics(self) -> ReviewAnalytics:
        """Retrieve review analytics data.

        Returns:
            ReviewAnalytics: Review analytics data.
        """
        total_reviews = await self.uow.reviews.count_all()
        pending_reviews = await self.uow.reviews.count_all(is_approved=False)
        approved_reviews = await self.uow.reviews.count_all(is_approved=True)
        average_rating = await self.uow.reviews.get_average_rating()

        return ReviewAnalytics(
            total_reviews=total_reviews,
            pending_reviews=pending_reviews,
            approved_reviews=approved_reviews,
            average_rating=average_rating,
        )

    async def get_dashboard_data(self) -> DashboardOverview:
        """Retrieve comprehensive dashboard data.

        Returns:
            DashboardOverview: Comprehensive dashboard data, including sales, users, products, and reviews.
        """
        sales = await self.get_sales_analytics()
        users = await self.get_user_analytics()
        products = await self.get_product_analytics()
        reviews = await self.get_review_analytics()

        return DashboardOverview(
            sales=sales,
            users=users,
            products=products,
            reviews=reviews,
        )

    async def get_all_orders(
        self,
        page: int = 1,
        page_size: int = 10,
        status: OrderStatus | None = None,
        user_id: UUID | None = None,
    ) -> Paged[OrderAdminRead]:
        """Retrieve all orders with pagination and optional filters.

        Args:
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 10.
            status (OrderStatus | None, optional): Filter by order status. Defaults to None.
            user_id (UUID | None, optional): Filter by user ID. Defaults to None.

        Returns:
            Paged[OrderAdminRead]: Paginated list of orders.
        """
        total, orders = await self.uow.orders.get_all_paginated(
            page=page, page_size=page_size, status=status, user_id=user_id
        )

        order_items = []

        for order in orders:
            order_items.append(
                OrderAdminRead(
                    id=order.id,
                    order_number=order.order_number,
                    user_id=order.user_id,
                    user_email=order.user.email,
                    total_amount=order.total_amount,
                    status=order.status.value,
                    payment_status=order.payment_status,
                    updated_at=order.updated_at,
                    created_at=order.created_at,
                    shipped_at=order.shipped_at,
                    paid_at=order.paid_at,
                    canceled_at=order.canceled_at,
                    delivered_at=order.delivered_at,
                )
            )

        return Paged[OrderAdminRead](
            items=order_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_order_status(self, order_id: UUID, new_status: OrderStatus) -> None:
        """Update the status of an order.

        Args:
            order_id (UUID): ID of the order to update.
            new_status (OrderStatus): New status to set for the order.
        """
        order = await self.uow.orders.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found.")

        # validate status transition
        allowed_transitions = self._ALLOWED_ORDER_STATUS_TRANSITIONS.get(order.status, set())
        if new_status not in allowed_transitions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition from {order.status} to {new_status}.",
            )

        # perform status update
        order.status = new_status
        if new_status == OrderStatus.SHIPPED:
            order.shipped_at = utcnow()
        elif new_status == OrderStatus.PAID:
            order.paid_at = utcnow()
        elif new_status == OrderStatus.CANCELED:
            order.canceled_at = utcnow()
        elif new_status == OrderStatus.DELIVERED:
            order.delivered_at = utcnow()
        else:
            raise HTTPException(status_code=400, detail="Invalid order status.")
        order.status = new_status
        await self.uow.orders.update(order)

    async def get_all_users(
        self,
        page: int = 1,
        page_size: int = 10,
        role: UserRole | None = None,
        search: str | None = None,
    ) -> Paged[UserAdminRead]:
        """Retrieve all users in the system.

        Returns:
            Paged[UserAdminRead]: Paginated list of all users.
        """
        total, users = await self.uow.users.get_all_paginated(
            page=page,
            page_size=page_size,
            role=role,
            search=search,
        )
        user_items = []
        for user in users:
            total_orders = await self.uow.orders.count_all(user_id=user.id)
            total_spent = await self.uow.orders.get_total_sales_by_user(user.id)

            user_items.append(
                UserAdminRead(
                    id=user.id,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role=user.role,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    is_superuser=user.is_superuser,
                    total_orders=total_orders,
                    total_spent=total_spent,
                )
            )

        return Paged[UserAdminRead](
            items=user_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_user_role(self, user_id: UUID, new_role: UserRole) -> None:
        """Update the role of a user.

        Args:
            user_id (UUID): ID of the user to update.
            new_role (UserRole): New role to set for the user.
        """
        user = await self.uow.users.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        user.role = new_role
        await self.uow.users.update(user)

    async def get_all_reviews(
        self,
        page: int = 1,
        page_size: int = 10,
        product_id: UUID | None = None,
        is_approved: bool | None = None,
        user_id: UUID | None = None,
        rating: int | None = None,
    ) -> Paged[ReviewAdminRead]:
        """Retrieve all product reviews with pagination and optional product filter.

        Returns:
            list[Review]: List of all product reviews.
        """
        total, reviews = await self.uow.reviews.get_all_paginated(
            page=page,
            page_size=page_size,
            product_id=product_id,
            is_approved=is_approved,
            user_id=user_id,
            rating=rating,
        )
        review_items = []
        for review in reviews:
            review_items.append(
                ReviewAdminRead(
                    id=review.id,
                    user_email=review.user.email,
                    product_name=review.product.name,
                    product_id=review.product_id,
                    user_id=review.user_id,
                    rating=review.rating,
                    comment=review.comment,
                    is_approved=review.is_approved,
                    created_at=review.created_at,
                    updated_at=review.updated_at,
                )
            )

        return Paged[ReviewAdminRead](
            items=review_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def approve_review(self, review_id: UUID) -> None:
        """Approve a product review.

        Args:
            review_id (UUID): ID of the review to approve.
        """
        review = await self.uow.reviews.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

        review.is_approved = True
        await self.uow.reviews.update(review)

    async def reject_review(self, review_id: UUID) -> None:
        """Reject (delete) a product review.

        Args:
            review_id (UUID): ID of the review to reject.
        """
        review = await self.uow.reviews.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

        await self.uow.reviews.delete_by_id(review.id)

    async def get_top_selling_products(self, limit: int = 10, days: int = 30) -> list[ProductRead]:
        """Retrieve top selling products.

        Args:
            limit (int): Number of top products to retrieve.
            days (int): Number of days to consider for sales data.

        Returns:
            list[ProductRead]: List of top selling products.
        """
        products = await self.uow.products.get_top_selling(limit=limit, days=days)
        return [ProductRead.model_validate(product) for product in products]

    async def get_low_stock_products(self, threshold: int = 10) -> list[ProductRead]:
        """Retrieve products that are low in stock.

        Args:
            threshold (int): Stock threshold.

        Returns:
            list[ProductRead]: List of low stock products.
        """
        products = await self.uow.products.get_low_stock(threshold=threshold)
        return [ProductRead.model_validate(product) for product in products]
