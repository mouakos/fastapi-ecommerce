"""Service module for address-related operations."""

from uuid import UUID

from app.core.exceptions import AddressNotFoundError, ResourceLimitError
from app.core.logger import logger
from app.interfaces.unit_of_work import UnitOfWork
from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate

MAX_ADDRESSES_PER_USER = 10


class AddressService:
    """Service class for address-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def get_addresses(self, user_id: UUID) -> list[Address]:
        """Get all Addresses for a user.

        Args:
            user_id (UUID): ID of the user owning the addresses.

        Returns:
            list[Address]: List of addresses associated with the user.

        """
        return await self.uow.addresses.list_all(user_id=user_id)

    async def get_address(self, address_id: UUID, user_id: UUID) -> Address:
        """Get an address for a specific user.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): ID of the user owning the address.

        Returns:
            Address: The address with the specified ID.

        Raises:
            AddressNotFoundError: If the address does not exists.
        """
        address = await self.uow.addresses.find_user_address(address_id, user_id)
        if not address:
            raise AddressNotFoundError(address_id=address_id, user_id=user_id)
        return address

    async def create_address(
        self,
        user_id: UUID,
        data: AddressCreate,
    ) -> Address:
        """Create a new address for a user.

        Args:
            user_id (UUID): ID of the user.
            data (AddressCreate): Address data including street, city, country, etc.

        Returns:
            Address: The created address.

        Raises:
            ResourceLimitError: If user has reached maximum address limit (10).
        """
        count = await self.uow.addresses.count(user_id=user_id)
        if count >= MAX_ADDRESSES_PER_USER:
            raise ResourceLimitError(
                resource="addresses",
                limit=MAX_ADDRESSES_PER_USER,
                current=count,
            )

        new_address = Address(**data.model_dump(), user_id=user_id)

        created_address = await self.uow.addresses.add(new_address)
        logger.info("address_created", user_id=str(user_id), address_id=str(created_address.id))
        return created_address

    async def update_address(self, address_id: UUID, user_id: UUID, data: AddressUpdate) -> Address:
        """Update an address for a user.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): ID of the user owning the address.
            data (AddressUpdate): The address data to update.

        Returns:
            Address: The updated address.

        Raises:
            AddressNotFoundError: If the address does not exist.
        """
        address = await self.get_address(address_id, user_id)

        address_data = data.model_dump(exclude_unset=True)

        for key, value in address_data.items():
            setattr(address, key, value)

        updated_address = await self.uow.addresses.update(address)
        logger.info("address_updated", user_id=str(user_id), address_id=str(address_id))
        return updated_address

    async def delete_address(self, address_id: UUID, user_id: UUID) -> None:
        """Delete an address for a user.

        Args:
            address_id (UUID): Address identifier.
            user_id (UUID): ID of the user owning the address.

        Raises:
            AddressNotFoundError: If the address does not exist.
        """
        address = await self.get_address(address_id, user_id)
        await self.uow.addresses.delete(address)
        logger.info("address_deleted", user_id=str(user_id), address_id=str(address_id))

    async def set_default_billing_address(self, address_id: UUID, user_id: UUID) -> Address:
        """Set an address as the default billing address for a user.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): ID of the user owning the address.

        Returns:
            Address: The updated address.

        Raises:
            AddressNotFoundError: If the address does not exist.
        """
        address = await self.get_address(address_id, user_id)
        await self.uow.addresses.unset_default_billing(user_id)

        address.is_default_billing = True

        updated_address = await self.uow.addresses.update(address)
        logger.info("default_billing_address_set", user_id=str(user_id), address_id=str(address_id))
        return updated_address

    async def set_default_shipping_address(self, address_id: UUID, user_id: UUID) -> Address:
        """Set an address as the default shipping address for a user.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): ID of the user owning the address.

        Returns:
            Address: The updated address.

        Raises:
            AddressNotFoundError: If the address does not exist.
        """
        address = await self.get_address(address_id, user_id)
        await self.uow.addresses.unset_default_shipping(user_id)

        address.is_default_shipping = True

        updated_address = await self.uow.addresses.update(address)
        logger.info(
            "default_shipping_address_set", user_id=str(user_id), address_id=str(address_id)
        )
        return updated_address
