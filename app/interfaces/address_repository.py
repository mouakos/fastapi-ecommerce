"""Interface for Address repository."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.address import Address


class AddressRepository(GenericRepository[Address], ABC):
    """Interface for Address repository."""

    @abstractmethod
    async def unset_default_billing(self, user_id: UUID) -> None:
        """Unset the default billing address for a user.

        Args:
            user_id (UUID): ID of the user owning the address.
        """
        ...

    @abstractmethod
    async def unset_default_shipping(self, user_id: UUID) -> None:
        """Unset the default shipping address for a user.

        Args:
            user_id (UUID): ID of the user owning the address.
        """
        ...

    @abstractmethod
    async def find_user_address(self, address_id: UUID, user_id: UUID) -> Address | None:
        """Find a user address by address ID and user ID.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): ID of the user owning the address.

        Returns:
            Address | None: The address if found, otherwise None.
        """
        ...
