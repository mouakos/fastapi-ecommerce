"""Interface for Payment repository."""

from abc import ABC, abstractmethod

from app.interfaces.generic_repository import GenericRepository
from app.models.payment import Payment


class PaymentRepository(GenericRepository[Payment], ABC):
    """Interface for Payment repository."""

    @abstractmethod
    async def find_by_transaction_id(self, transaction_id: str) -> Payment | None:
        """Find a payment by transaction ID.

        Args:
            transaction_id (str): Transaction ID.

        Returns:
            Payment | None: Payment record or None.
        """
        ...
