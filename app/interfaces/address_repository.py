"""Interface for Address repository."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.address import Address


class AddressRepository(GenericRepository[Address], ABC):
    """Interface for Address repository."""

    @abstractmethod
    async def unset_user_default_shipping_address(self, user_id: UUID) -> None:
        """Unset the default shipping address for a user.

        Args:
            user_id (UUID): The ID of the user.
        """
        raise NotImplementedError()

    @abstractmethod
    async def unset_user_default_billing_address(self, user_id: UUID) -> None:
        """Unset the default billing address for a user.

        Args:
            user_id (UUID): The ID of the user.
        """
        raise NotImplementedError()
