"""Interface for Order repository."""

from abc import ABC, abstractmethod
from decimal import Decimal
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.order import Order, OrderStatus


class OrderRepository(GenericRepository[Order], ABC):
    """Interface for Order repository."""

    @abstractmethod
    async def calculate_total_sales(self) -> Decimal:
        """Calculate total sales amount.

        Returns:
            Decimal: Total sales amount.
        """
        ...

    @abstractmethod
    async def find_user_order(self, order_id: UUID, user_id: UUID) -> Order | None:
        """Find an order by ID for a specific user.

        Args:
            order_id (UUID): Order ID.
            user_id (UUID): User ID.

        Returns:
            Order | None: Order record or None.
        """

    @abstractmethod
    async def calculate_recent_sales(self, days: int) -> Decimal:
        """Calculate total sales amount over the last specified number of days.

        Args:
            days (int): Number of days to look back.

        Returns:
            Decimal: Total sales amount over the last specified number of days.
        """
        ...

    @abstractmethod
    async def calculate_user_sales(self, user_id: UUID) -> Decimal:
        """Calculate total sales amount for a specific user.

        Args:
            user_id (UUID): User ID.

        Returns:
            Decimal: Total sales amount for the specified user.
        """
        ...

    @abstractmethod
    async def find_all(
        self,
        *,
        status: OrderStatus | None = None,
        user_id: UUID | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Order], int]:
        """Find all orders with optional filters, sorting, and pagination.

        Args:
            status (OrderStatus | None, optional): Filter by order status. Defaults to None.
            user_id (UUID | None, optional): Filter by user ID. Defaults to None.
            sort_by (str, optional): Field to sort by. Defaults to "created_at".
            sort_order (str, optional): Sort order, either "asc" or "desc". Defaults to "desc".
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 10.

        Returns:
            tuple[list[Order], int]: List of orders and total count.
        """
        ...
