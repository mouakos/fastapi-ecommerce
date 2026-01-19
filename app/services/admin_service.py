"""Service layer for admin-related operations."""

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException

from app.interfaces.unit_of_work import UnitOfWork
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.review import Review, ReviewStatus
from app.models.user import User, UserRole
from app.schemas.statistics import (
    AdminDashboard,
    ProductStatistics,
    ReviewStatistics,
    SalesStatistics,
    UserStatistics,
)
from app.utils.order_utils import is_valid_order_status_transition
from app.utils.utc_time import utcnow


class AdminService:
    """Service class for admin-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    # ----------------------------- Statistics Related Admin Services ----------------------------- #
    async def get_sales_statistics(self) -> SalesStatistics:
        """Calculate sales statistics data.

        Returns:
            SalesStatistics: Sales statistics data.
        """
        # Total orders and revenue
        total_orders = await self.uow.orders.count()
        total_revenue = await self.uow.orders.calculate_total_sales()

        # Orders by status
        pending_orders = await self.uow.orders.count(status=OrderStatus.PENDING)
        paid_orders = await self.uow.orders.count(status=OrderStatus.PAID)
        shipped_orders = await self.uow.orders.count(status=OrderStatus.SHIPPED)
        delivered_orders = await self.uow.orders.count(status=OrderStatus.DELIVERED)
        cancelled_orders = await self.uow.orders.count(status=OrderStatus.CANCELED)

        # Average order value
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0.0

        # Revenue in the last 30 days
        revenue_last_30_days = await self.uow.orders.calculate_recent_sales(days=30)

        return SalesStatistics(
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

    async def get_user_statistics(self) -> UserStatistics:
        """Calculate user statistics data.

        Returns:
            UserStatistics: User statistics data.
        """
        total_users = await self.uow.users.count()
        total_customers = await self.uow.users.count(role=UserRole.USER)
        total_admins = await self.uow.users.count(role=UserRole.ADMIN)

        # New users in the last 30 days
        new_users_last_30_days = await self.uow.users.count_recent(days=30)

        return UserStatistics(
            total_users=total_users,
            total_customers=total_customers,
            total_admins=total_admins,
            new_users_last_30_days=new_users_last_30_days,
        )

    async def get_product_statistics(self) -> ProductStatistics:
        """Calculate product statistics data.

        Returns:
            ProductStatistics: Product statistics data.
        """
        total_products = await self.uow.products.count()
        active_products = await self.uow.products.count(is_active=True)
        inactive_products = await self.uow.products.count(is_active=False)
        out_of_stock_count = await self.uow.products.count(stock=0)
        low_stock_count = await self.uow.products.count_low_stock(threshold=10)

        return ProductStatistics(
            total_products=total_products,
            active_products=active_products,
            inactive_products=inactive_products,
            out_of_stock_count=out_of_stock_count,
            low_stock_count=low_stock_count,
        )

    async def get_review_statistics(self) -> ReviewStatistics:
        """Calculate review statistics data.

        Returns:
            ReviewStatistics: Review statistics data.
        """
        total_reviews = await self.uow.reviews.count()
        pending_reviews = await self.uow.reviews.count(status=ReviewStatus.PENDING)
        approved_reviews = await self.uow.reviews.count(status=ReviewStatus.APPROVED)
        average_rating = await self.uow.reviews.calculate_average_rating()

        return ReviewStatistics(
            total_reviews=total_reviews,
            pending_reviews=pending_reviews,
            approved_reviews=approved_reviews,
            average_rating=average_rating,
        )

    async def get_dashboard_data(self) -> AdminDashboard:
        """Calculate comprehensive dashboard data.

        Returns:
            AdminDashboard: Comprehensive dashboard data, including sales, users, products, and reviews.
        """
        sales = await self.get_sales_statistics()
        users = await self.get_user_statistics()
        products = await self.get_product_statistics()
        reviews = await self.get_review_statistics()

        return AdminDashboard(
            sales=sales,
            users=users,
            products=products,
            reviews=reviews,
        )

    # ----------------------------- Order Related Admin Services ----------------------------- #
    async def list_orders(
        self,
        page: int = 1,
        page_size: int = 10,
        status: OrderStatus | None = None,
        user_id: UUID | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Order], int]:
        """List all orders with pagination and optional filters.

        Args:
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 10.
            status (OrderStatus | None, optional): Filter by order status. Defaults to None.
            user_id (UUID | None, optional): Filter by user ID. Defaults to None.
            sort_by (str, optional): Field to sort by. Defaults to "created_at".
            sort_order (str, optional): Sort order, either "asc" or "desc".

        Returns:
            tuple[list[Order], int]: List of orders and total count.
        """
        orders, total = await self.uow.orders.paginate(
            page=page,
            page_size=page_size,
            status=status,
            user_id=user_id,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return orders, total

    async def update_order_status(self, order_id: UUID, new_status: OrderStatus) -> None:
        """Update the status of an order.

        Args:
            order_id (UUID): ID of the order to update.
            new_status (OrderStatus): New status to set for the order.
        """
        order = await self.uow.orders.find_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found.")

        # validate status transition
        is_valid_transition = is_valid_order_status_transition(order.status, new_status)
        if not is_valid_transition:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid order status transition from {order.status} to {new_status}.",
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

    # ----------------------------- User Related Admin Services ----------------------------- #
    async def list_users(
        self,
        page: int = 1,
        page_size: int = 10,
        role: UserRole | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[User], int]:
        """List all users in the system.

        Args:
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 10.
            role (UserRole | None, optional): Filter by user role. Defaults to None.
            search (str | None, optional): Search query for name or email. Defaults to None.
            sort_by (str, optional): Field to sort by. Defaults to "created_at".
            sort_order (str, optional): Sort order, either "asc" or "desc". Defaults to "desc".

        Returns:
            tuple[list[User], int]: List of users and total number of users.
        """
        users, total = await self.uow.users.paginate(
            page=page,
            page_size=page_size,
            role=role,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return users, total

    async def count_user_orders(self, user_id: UUID) -> int:
        """Count the total number of orders placed by a user.

        Args:
            user_id (UUID): ID of the user.

        Returns:
            int: Total number of orders placed by the user.
        """
        return await self.uow.orders.count(user_id=user_id)

    async def get_user_total_spent(self, user_id: UUID) -> Decimal:
        """Calculate the total amount spent by a user across all orders.

        Args:
            user_id (UUID): ID of the user.

        Returns:
            Decimal: Total amount spent by the user.
        """
        return await self.uow.orders.calculate_user_sales(user_id)

    async def update_user_role(self, user_id: UUID, new_role: UserRole) -> None:
        """Update the role of a user.

        Args:
            user_id (UUID): ID of the user to update.
            new_role (UserRole): New role to set for the user.
        """
        user = await self.uow.users.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        if user.role == new_role:
            return

        user.role = new_role
        await self.uow.users.update(user)

    # ----------------------------- Review Related Admin Services ----------------------------- #
    async def list_reviews(
        self,
        page: int = 1,
        page_size: int = 10,
        product_id: UUID | None = None,
        status: ReviewStatus | None = None,
        user_id: UUID | None = None,
        rating: int | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Review], int]:
        """List all product reviews with pagination and optional product filter.

        Args:
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 10.
            product_id (UUID | None, optional): Filter by product ID. Defaults to None.
            status (ReviewStatus | None, optional): Filter by review status. Defaults to None.
            user_id (UUID | None, optional): Filter by user ID. Defaults to None.
            rating (int | None, optional): Filter by rating. Defaults to None.
            sort_by (str, optional): Field to sort by. Defaults to "created_at".
            sort_order (str, optional): Sort order. Defaults to "desc".

        Returns:
            tuple[list[Review], int]: List of reviews and total count.

        Raises:
            HTTPException: If the product is not found.
        """
        if product_id:
            product = await self.uow.products.find_by_id(product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Product not found.")

        reviews, total = await self.uow.reviews.paginate(
            page=page,
            page_size=page_size,
            product_id=product_id,
            status=status,
            user_id=user_id,
            rating=rating,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return reviews, total

    async def approve_review(self, review_id: UUID, moderator_id: UUID) -> Review:
        """Approve a product review.

        Args:
            review_id (UUID): ID of the review to approve.
            moderator_id (UUID): ID of the admin approving the review.

        Returns:
            Review: The updated review instance.
        """
        review = await self.uow.reviews.find_by_id(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

        # Approve the review
        review.status = ReviewStatus.APPROVED
        review.moderated_at = utcnow()
        review.moderated_by = moderator_id

        return await self.uow.reviews.update(review)

    async def reject_review(self, review_id: UUID, moderator_id: UUID) -> Review:
        """Reject a product review.

        Args:
            review_id (UUID): ID of the review to reject.
            moderator_id (UUID): ID of the admin rejecting the review.

        Returns:
            Review: The updated review instance.
        """
        review = await self.uow.reviews.find_by_id(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

        # Reject the review
        review.status = ReviewStatus.REJECTED
        review.moderated_at = utcnow()
        review.moderated_by = moderator_id

        return await self.uow.reviews.update(review)

    async def delete_review(self, review_id: UUID) -> None:
        """Delete a product review.

        Args:
            review_id (UUID): ID of the review to delete.
        """
        review = await self.uow.reviews.find_by_id(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")
        await self.uow.reviews.delete(review)

    # ---------------- Product Related Admin Services ---------------- #

    async def list_products(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        category_id: UUID | None = None,
        category_slug: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        min_rating: float | None = None,
        availability: str = "all",
        is_active: bool | None = None,
        sort_by: str = "created_at",
        sort_order: str = "asc",
    ) -> tuple[list[Product], int]:
        """List all products with pagination and optional filters.

        Args:
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 10.
            search (str | None, optional): Search query to filter products by name or description. Defaults to None.
            category_id (UUID | None, optional): Category ID to filter products. Defaults to None.
            category_slug (str | None, optional): Category slug to filter products. Defaults to None.
            min_price (Decimal | None, optional): Minimum price to filter products. Defaults to None.
            max_price (Decimal | None, optional): Maximum price to filter products. Defaults to None.
            min_rating (float | None, optional): Minimum average rating to filter products. Defaults to None.
            availability (str, optional): Stock availability filter ("in_stock", "out_of_stock", "all"). Defaults to "all".
            is_active (bool | None, optional): Filter by active status. Defaults to None.
            sort_by (str, optional): Field to sort by. Defaults to "created_at".
            sort_order (str, optional): Sort order ("asc" or "desc"). Defaults to "asc".

        Returns:
            tuple[list[Product], int]: List of products and total count.
        """
        return await self.uow.products.paginate(
            page=page,
            page_size=page_size,
            search=search,
            category_id=category_id,
            category_slug=category_slug,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            is_active=is_active,
            availability=availability,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def list_top_selling_products(self, limit: int = 10, days: int = 30) -> list[Product]:
        """Retrieve top selling products.

        Args:
            limit (int): Number of top products to retrieve.
            days (int): Number of days to consider for sales data.

        Returns:
            list[Product]: List of top selling products.
        """
        return await self.uow.products.list_top_selling(limit=limit, days=days)

    async def list_low_stock_products(
        self, threshold: int = 10, is_active: bool | None = None, page: int = 1, page_size: int = 10
    ) -> tuple[list[Product], int]:
        """Retrieve products that are low in stock.

        Args:
            threshold (int, optional): Stock threshold. Defaults to 10.
            is_active (bool | None, optional): Filter by active status. Defaults to None.
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of products per page. Defaults to 10.

        Returns:
            tuple[list[Product], int]: List of low stock products and total count.
        """
        return await self.uow.products.paginate_low_stock(
            threshold=threshold, is_active=is_active, page=page, page_size=page_size
        )
