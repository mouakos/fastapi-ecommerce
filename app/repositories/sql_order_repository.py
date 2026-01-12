"""SQLModel User repository implementation."""

from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.order_repository import OrderRepository
from app.models.order import Order
from app.repositories.sql_generic_repository import SqlGenericRepository


class SqlOrderRepository(SqlGenericRepository[Order], OrderRepository):
    """SQL Order repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, Order)
