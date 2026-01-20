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
        """Find an address by ID with user ownership validation.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): User ID for ownership validation.

        Returns:
            Address | None: The address if found and owned by user, otherwise None.
        """
        ...
