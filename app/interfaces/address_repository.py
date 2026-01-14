"""Interface for Address repository."""

from abc import ABC, abstractmethod
from typing import Literal
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.address import Address

AddressType = Literal["shipping", "billing"]


class AddressRepository(GenericRepository[Address], ABC):
    """Interface for Address repository."""

    @abstractmethod
    async def unset_default(self, user_id: UUID, address_type: AddressType) -> None:
        """Unset the default address for a user and address type.

        Args:
            user_id (UUID): User ID.
            address_type (AddressType): Address type (shipping or billing).

        Raises:
            ValueError: If the address type is invalid.
        """
        raise NotImplementedError()
