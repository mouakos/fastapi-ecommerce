"""Interface for Payment repository."""

from abc import ABC, abstractmethod

from app.interfaces.generic_repository import GenericRepository
from app.models.payment import Payment


class PaymentRepository(GenericRepository[Payment], ABC):
    """Interface for Payment repository."""

    @abstractmethod
    async def find_by_session_id(self, session_id: str) -> Payment | None:
        """Find a payment by session ID.

        Args:
            session_id (str): Session ID.

        Returns:
            Payment | None: Payment or none.
        """
        ...
