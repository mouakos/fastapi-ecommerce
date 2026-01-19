"""SQL Payment repository implementation."""

from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.payment_repository import PaymentRepository
from app.models.payment import Payment
from app.repositories.sql_generic_repository import SqlGenericRepository


class SqlPaymentRepository(SqlGenericRepository[Payment], PaymentRepository):
    """SQL Payment repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, Payment)

    async def find_by_session_id(self, session_id: str) -> Payment | None:
        """Find a payment by Stripe session ID.

        Args:
            session_id (str): Stripe session ID.

        Returns:
            Payment | None: Payment record or None.
        """
        from sqlmodel import select

        stmt = select(Payment).where(Payment.session_id == session_id)
        result = await self._session.exec(stmt)
        return result.first()
