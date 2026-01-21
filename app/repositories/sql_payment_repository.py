"""SQL Payment repository implementation."""

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.payment_repository import PaymentRepository
from app.models.payment import Payment
from app.repositories.sql_generic_repository import SqlGenericRepository


class SqlPaymentRepository(SqlGenericRepository[Payment], PaymentRepository):
    """SQL Payment repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, Payment)

    async def find_by_transaction_id(self, transaction_id: str) -> Payment | None:
        """Find a payment by transaction ID.

        Args:
            transaction_id (str): Transaction ID.

        Returns:
            Payment | None: Payment record or None.
        """
        stmt = select(Payment).where(Payment.transaction_id == transaction_id)
        result = await self._session.exec(stmt)
        return result.first()
