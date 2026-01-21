"""Service layer for admin-related operations."""

from decimal import Decimal
from uuid import UUID

from app.core.exceptions import (
    InvalidTransitionError,
    OrderNotFoundError,
    ReviewNotFoundError,
    SelfActionError,
    UserNotFoundError,
)
from app.core.logger import logger
from app.interfaces.unit_of_work import UnitOfWork
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.review import Review, ReviewStatus
from app.models.user import User, UserRole
from app.schemas.analytics import (
    AdminDashboard,
    ProductAnalytics,
    ReviewAnalytics,
    SalesAnalytics,
    UserAnalytics,
)
from app.utils.datetime import utcnow
from app.utils.order import is_valid_order_status_transition


class AdminService:
    """Service class for admin-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    # ----------------------------- Analytics Related Admin Services ----------------------------- #
    async def get_sales_analytics(self) -> SalesAnalytics:
        """Get sales analytics data.

        Returns:
            SalesAnalytics: Sales analytics data.
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
        """Get user analytics data.

        Returns:
            UserAnalytics: User analytics data.
        """
        total_users = await self.uow.users.count()
        total_customers = await self.uow.users.count(role=UserRole.USER)
        total_admins = await self.uow.users.count(role=UserRole.ADMIN)

        # New users in the last 30 days
        new_users_last_30_days = await self.uow.users.count_recent(days=30)

        return UserAnalytics(
            total_users=total_users,
            total_customers=total_customers,
            total_admins=total_admins,
            new_users_last_30_days=new_users_last_30_days,
        )

    async def get_product_analytics(self) -> ProductAnalytics:
        """Get product analytics data.

        Returns:
            ProductAnalytics: Product analytics data.
        """
        total_products = await self.uow.products.count()
        active_products = await self.uow.products.count(is_active=True)
        inactive_products = await self.uow.products.count(is_active=False)
        out_of_stock_count = await self.uow.products.count(stock=0)
        low_stock_count = await self.uow.products.count_low_stock(threshold=10)

        return ProductAnalytics(
            total_products=total_products,
            active_products=active_products,
            inactive_products=inactive_products,
            out_of_stock_count=out_of_stock_count,
            low_stock_count=low_stock_count,
        )

    async def get_review_analytics(self) -> ReviewAnalytics:
        """Get review analytics data.

        Returns:
            ReviewAnalytics: Review analytics data.
        """
        total_reviews = await self.uow.reviews.count()
        pending_reviews = await self.uow.reviews.count(status=ReviewStatus.PENDING)
        approved_reviews = await self.uow.reviews.count(status=ReviewStatus.APPROVED)
        average_rating = await self.uow.reviews.calculate_average_rating()

        return ReviewAnalytics(
            total_reviews=total_reviews,
            pending_reviews=pending_reviews,
            approved_reviews=approved_reviews,
            average_rating=average_rating,
        )

    async def get_dashboard_data(self) -> AdminDashboard:
        """Get comprehensive dashboard data.

        Returns:
            AdminDashboard: Comprehensive dashboard data, including sales, users, products, and reviews.
        """
        sales = await self.get_sales_analytics()
        users = await self.get_user_analytics()
        products = await self.get_product_analytics()
        reviews = await self.get_review_analytics()
        return AdminDashboard(
            sales=sales,
            users=users,
            products=products,
            reviews=reviews,
        )

    # ----------------------------- Order Related Admin Services ----------------------------- #
    async def get_orders(
        self,
        status: OrderStatus | None = None,
        user_id: UUID | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Order], int]:
        """Get all orders with pagination and optional filters, sorting and pagination.

        Args:
            status (OrderStatus | None, optional): Filter by order status. Defaults to None.
            user_id (UUID | None, optional): Filter by user ID. Defaults to None.
            sort_by (str, optional): Field to sort by. Defaults to "created_at".
            sort_order (str, optional): Sort order, either "asc" or "desc".
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of orders per page. Defaults to 10.

        Returns:
            tuple[list[Order], int]: List of orders and total count.
        """
        orders, total = await self.uow.orders.find_all(
            page=page,
            page_size=page_size,
            status=status,
            user_id=user_id,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return orders, total

    async def update_order_status(self, order_id: UUID, new_status: OrderStatus) -> None:
        """Update order status with validation and timestamp tracking.

        Validates status transitions and updates corresponding timestamp fields
        (shipped_at, paid_at, canceled_at, delivered_at).

        Args:
            order_id (UUID): ID of the order to update.
            new_status (OrderStatus): New status (PENDING, PAID, SHIPPED, DELIVERED, CANCELED).

        Raises:
            OrderNotFoundError: If order not found.
        """
        order = await self.uow.orders.find_by_id(order_id)
        if not order:
            raise OrderNotFoundError(order_id=order_id)

        # validate status transition
        is_valid_transition = is_valid_order_status_transition(order.status, new_status)
        if not is_valid_transition:
            raise InvalidTransitionError(
                entity="Order", from_state=order.status, to_state=new_status
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
            raise InvalidTransitionError(
                entity="Order", from_state=order.status, to_state=new_status
            )
        order.status = new_status
        await self.uow.orders.update(order)
        logger.info("OrderStatusUpdated", order_id=str(order_id), new_status=new_status.value)

    # ----------------------------- User Related Admin Services ----------------------------- #
    async def get_users(
        self,
        role: UserRole | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[User], int]:
        """Get all users in the system with optional filters, sorting, and pagination.

        Args:
            role (UserRole | None, optional): Filter by user role. Defaults to None.
            search (str | None, optional): Search query for name or email. Defaults to None.
            sort_by (str, optional): Field to sort by. Defaults to "created_at".
            sort_order (str, optional): Sort order, either "asc" or "desc". Defaults to "desc".
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 10.


        Returns:
            tuple[list[User], int]: List of users and total number of users.
        """
        users, total = await self.uow.users.find_all(
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

    async def update_user_role(
        self, current_user_id: UUID, user_id: UUID, new_role: UserRole
    ) -> None:
        """Update a user's role.

        Args:
            current_user_id (UUID): ID of the user making the request.
            user_id (UUID): ID of the user to update.
            new_role (UserRole): New role to set for the user.

        Raises:
            UserNotFoundError: If the user is not found.
            SelfActionError: If trying to change own role.
        """
        user = await self.uow.users.find_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        if user_id == current_user_id:
            raise SelfActionError(action="changing your own role")

        if user.role == new_role:
            return

        user.role = new_role
        await self.uow.users.update(user)
        logger.info(
            "UserRoleUpdated",
            user_id=str(user_id),
            new_role=new_role.value,
            updated_by=str(current_user_id),
        )

    # ----------------------------- Review Related Admin Services ----------------------------- #
    async def get_reviews(
        self,
        product_id: UUID | None = None,
        status: ReviewStatus | None = None,
        user_id: UUID | None = None,
        rating: int | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Review], int]:
        """Get all product reviews with optional filters, sorting, and pagination.

        Args:
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 10.
            product_id (UUID | None, optional): Filter by product ID. Defaults to None.
            status (ReviewStatus | None, optional): Filter by review status. Defaults to None.
            user_id (UUID | None, optional): Filter by user ID. Defaults to None.
            rating (int | None, optional): Filter by rating. Defaults to None.
            sort_by (str, optional): Field to sort by. Defaults to "created_at".
            sort_order (str, optional): Sort order. Defaults to "desc".
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of reviews per page. Defaults to 10.

        Returns:
            tuple[list[Review], int]: List of reviews and total count.
        """
        reviews, total = await self.uow.reviews.find_all(
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
        """Approve a review to make it publicly visible.

        Sets status to APPROVED and records moderator ID and timestamp.

        Args:
            review_id (UUID): ID of the review to approve.
            moderator_id (UUID): ID of the admin performing the approval.

        Returns:
            Review: The approved review with updated moderation metadata.

        Raises:
            ReviewNotFoundError: If review is not found.
        """
        review = await self.uow.reviews.find_by_id(review_id)
        if not review:
            raise ReviewNotFoundError(review_id=review_id)

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
            raise ReviewNotFoundError(review_id=review_id)

        # Reject the review
        review.status = ReviewStatus.REJECTED
        review.moderated_at = utcnow()
        review.moderated_by = moderator_id

        updated_review = await self.uow.reviews.update(review)
        logger.info("ReviewRejected", review_id=str(review_id), moderator_id=str(moderator_id))
        return updated_review

    async def delete_review(self, review_id: UUID) -> None:
        """Delete a product review.

        Args:
            review_id (UUID): ID of the review to delete.

        Raises:
            ReviewNotFoundError: If review is not found.
        """
        review = await self.uow.reviews.find_by_id(review_id)
        if not review:
            raise ReviewNotFoundError(review_id=review_id)
        await self.uow.reviews.delete(review)
        logger.info("ReviewDeleted", review_id=str(review_id))

    # ---------------- Product Related Admin Services ---------------- #

    async def get_products(
        self,
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
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Product], int]:
        """Get all products with optional filters, sorting, and pagination.

        Args:
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
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 10.

        Returns:
            tuple[list[Product], int]: List of products and total count.
        """
        return await self.uow.products.find_all(
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

    async def get_top_selling_products(self, limit: int = 10, days: int = 30) -> list[Product]:
        """Get top selling products.

        Args:
            limit (int): Number of top products to retrieve.
            days (int): Number of days to consider for sales data.

        Returns:
            list[Product]: List of top selling products.
        """
        return await self.uow.products.list_top_selling(limit=limit, days=days)

    async def get_low_stock_products(
        self, threshold: int = 10, is_active: bool | None = None, page: int = 1, page_size: int = 10
    ) -> tuple[list[Product], int]:
        """Get products with stock below specified threshold for inventory alerts.

        Args:
            threshold (int): Stock quantity threshold for low stock alert. Defaults to 10.
            is_active (bool | None): Filter by active status (True, False, or None for all). Defaults to None.
            page (int): Page number for pagination. Defaults to 1.
            page_size (int): Items per page. Defaults to 10.

        Returns:
            tuple[list[Product], int]: List of low stock products and total count.
        """
        return await self.uow.products.list_low_stock(
            threshold=threshold, is_active=is_active, page=page, page_size=page_size
        )
