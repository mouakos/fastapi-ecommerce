"""Interface for Order repository."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.order import Order, OrderStatus


class OrderRepository(GenericRepository[Order], ABC):
    """Interface for Order repository."""

    @abstractmethod
    async def user_has_purchased_product(self, user_id: UUID, product_id: UUID) -> bool:
        """Check if a user has ordered a specific product.

        Args:
            user_id (UUID): User ID.
            product_id (UUID): Product ID.

        Returns:
            bool: True if the user has ordered the product, False otherwise.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_total_sales(self) -> Decimal:
        """Get total sales amount.

        Returns:
            Decimal: Total sales amount.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_total_sales_by_last_days(self, days: int) -> Decimal:
        """Get total sales amount over the last specified number of days.

        Args:
            days (int): Number of days to look back.

        Returns:
            Decimal: Total sales amount over the last specified number of days.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_total_sales_by_user(self, user_id: UUID) -> Decimal:
        """Get total sales amount for a specific user.

        Args:
            user_id (UUID): User ID.

        Returns:
            Decimal: Total sales amount for the specified user.
        """
        raise NotImplementedError()

    @abstractmethod
    async def count_all(self, **filters: Any) -> int:  # noqa: ANN401
        """Get total number of orders.

        Args:
            **filters: Filter conditions.

        Returns:
            int: Total number of orders.

        Raises:
            ValueError: If invalid filters are provided.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_all_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        status: OrderStatus | None = None,
        user_id: UUID | None = None,
    ) -> tuple[int, list[Order]]:  # noqa: ANN401
        """Get all orders with pagination and optional filters.

        Args:
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 100.
            status (OrderStatus | None, optional): Filter by order status. Defaults to None.
            user_id (UUID | None, optional): Filter by user ID. Defaults to None.

        Returns:
            tuple[int, list[Order]]: Total count and list of orders.
        """
        raise NotImplementedError()
