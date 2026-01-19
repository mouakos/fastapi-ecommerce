"""Interface for Payment repository."""

from abc import ABC

from app.interfaces.generic_repository import GenericRepository
from app.models.payment import Payment


class PaymentRepository(GenericRepository[Payment], ABC):
    """Interface for Payment repository."""

    async def find_by_session_id(self, session_id: str) -> Payment | None:
        """Find a payment by Stripe session ID.

        Args:
            session_id (str): Stripe session ID.

        Returns:
            Payment | None: Payment record or None.
        """
        ...
