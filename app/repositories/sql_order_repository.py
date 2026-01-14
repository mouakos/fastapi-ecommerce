"""SQL User repository implementation."""

from decimal import Decimal
from typing import Any
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

    async def get_total_sales(self) -> Decimal:
        """Get total sales amount.

        Returns:
            Decimal: Total sales amount.
        """
        stmt = select(func.sum(Order.total_amount)).where(Order.status == OrderStatus.PAID)
        result = await self._session.exec(stmt)
        total = result.first()
        return total or Decimal("0.00")

    async def get_total_sales_by_last_days(self, days: int) -> Decimal:
        """Get total sales amount over the last specified number of days.

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
        total = result.first()
        return total or Decimal("0.00")

    async def get_total_sales_by_user(self, user_id: UUID) -> Decimal:
        """Get total sales amount for a specific user.

        Args:
            user_id (UUID): User ID.

        Returns:
            Decimal: Total sales amount for the specified user.
        """
        stmt = select(func.sum(Order.total_amount)).where(
            Order.user_id == user_id, Order.status == OrderStatus.PAID
        )
        result = await self._session.exec(stmt)
        total = result.first()
        return total or Decimal("0.00")

    async def count_all(self, **filters: Any) -> int:  # noqa: ANN401
        """Get total number of orders.

        Args:
            **filters: Filter conditions.

        Returns:
            int: Total number of orders.
        """
        stmt = select(func.count()).select_from(Order)

        for attr, value in filters.items():
            if not hasattr(Order, attr):
                raise ValueError(f"Invalid filter condition: {attr}")
            stmt = stmt.where(getattr(Order, attr) == value)

        result = await self._session.exec(stmt)
        return result.first() or 0

    async def get_all_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        status: OrderStatus | None = None,
        user_id: UUID | None = None,
    ) -> tuple[int, list[Order]]:
        """Get all orders with pagination and optional filters.

        Args:
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 100.
            status (OrderStatus | None, optional): Filter by order status. Defaults to None.
            user_id (UUID | None, optional): Filter by user ID. Defaults to None.

        Returns:
            tuple[int, list[Order]]: Total count and list of orders.
        """
        # Build the base query
        stmt = select(Order)

        # Apply filters
        if status is not None:
            stmt = stmt.where(Order.status == status)

        if user_id is not None:
            stmt = stmt.where(Order.user_id == user_id)

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

        return total, orders
