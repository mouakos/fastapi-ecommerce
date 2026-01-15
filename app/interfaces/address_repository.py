"""Interface for Address repository."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.address import Address


class AddressRepository(GenericRepository[Address], ABC):
    """Interface for Address repository."""

    @abstractmethod
    async def unset_default_billing_for_user(self, user_id: UUID) -> None:
        """Unset the default billing address for a user.

        Args:
            user_id (UUID): User ID.
        """
        raise NotImplementedError()

    @abstractmethod
    async def unset_default_shipping_for_user(self, user_id: UUID) -> None:
        """Unset the default shipping address for a user.

        Args:
            user_id (UUID): User ID.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_for_user(self, address_id: UUID, user_id: UUID) -> Address | None:
        """Get a single address for a user.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): User ID.

        Returns:
            Address | None: The address if found, otherwise None.
        """
        raise NotImplementedError()

    @abstractmethod
    async def count_all(self, **filters: Any) -> int:  # noqa: ANN401
        """Count all addresses matching the given filters.

        Args:
            **filters: Filter conditions.

        Returns:
            int: The count of addresses matching the filters.

        Raises:
            ValueError: Invalid filter condition.
        """
        raise NotImplementedError()
