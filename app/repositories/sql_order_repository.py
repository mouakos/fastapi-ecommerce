"""SQL User repository implementation."""

from decimal import Decimal
from uuid import UUID

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.order_repository import OrderRepository
from app.models.order import Order, OrderStatus
from app.repositories.sql_generic_repository import SqlGenericRepository


class SqlOrderRepository(SqlGenericRepository[Order], OrderRepository):
    """SQL Order repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, Order)

    async def calculate_total_sales(self) -> Decimal:
        """Calculate total sales amount.

        Returns:
            Decimal: Total sales amount.
        """
        stmt = select(func.sum(Order.total_amount)).where(Order.status == OrderStatus.PAID)
        result = await self._session.exec(stmt)
        return result.first() or Decimal("0.00")

    async def calculate_recent_sales(self, days: int) -> Decimal:
        """Calculate total sales amount over the last specified number of days.

        Args:
            days (int): Number of days to look back.

        Returns:
            Decimal: Total sales amount over the last specified number of days.
        """
        stmt = select(func.sum(Order.total_amount)).where(
            Order.status == OrderStatus.PAID,
            func.now() - Order.created_at <= func.make_interval(0, 0, 0, days, 0, 0, 0),
        )
        result = await self._session.exec(stmt)
        return result.first() or Decimal("0.00")

    async def calculate_user_sales(self, user_id: UUID) -> Decimal:
        """Calculate total sales amount for a specific user.

        Args:
            user_id (UUID): User ID.

        Returns:
            Decimal: Total sales amount for the specified user.
        """
        stmt = select(func.sum(Order.total_amount)).where(
            Order.user_id == user_id, Order.status == OrderStatus.PAID
        )
        result = await self._session.exec(stmt)
        return result.first() or Decimal("0.00")

    async def paginate(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        status: OrderStatus | None = None,
        user_id: UUID | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Order], int]:
        """Get all orders with pagination and optional filters.

        Args:
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 10.
            status (OrderStatus | None, optional): Filter by order status. Defaults to None.
            user_id (UUID | None, optional): Filter by user ID. Defaults to None.
            sort_by (str, optional): Field to sort by. Defaults to "created_at".
            sort_order (str, optional): Sort order, either "asc" or "desc". Defaults to "desc".

        Returns:
            tuple[list[Order], int]: List of orders and total count.
        """
        # Build the base query
        stmt = select(Order)

        # Apply filters
        if status is not None:
            stmt = stmt.where(Order.status == status)

        if user_id is not None:
            stmt = stmt.where(Order.user_id == user_id)

        # Apply sorting
        sort_column = {
            "created_at": Order.created_at,
            "total_amount": Order.total_amount,
            "status": Order.status,
        }.get(sort_by, Order.created_at)
        sort_column = sort_column.desc() if sort_order == "desc" else sort_column.asc()  # type: ignore [attr-defined]
        stmt = stmt.order_by(sort_column)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self._session.exec(count_stmt)
        total = count_result.first() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        # Execute query
        result = await self._session.exec(stmt)
        orders = list(result.all())

        return orders, total
