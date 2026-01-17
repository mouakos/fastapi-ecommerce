"""Service module for address-related operations."""

from uuid import UUID

from fastapi import HTTPException, status

from app.interfaces.unit_of_work import UnitOfWork
from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate

MAX_ADDRESSES_PER_USER = 10


class AddressService:
    """Service class for address-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def list(self, user_id: UUID) -> list[Address]:
        """List all Addresses for a user.

        Args:
            user_id (UUID): ID of the user owning the addresses.

        Returns:
            list[Address]: List of addresses associated with the user.

        """
        return await self.uow.addresses.list_all(user_id=user_id)

    async def find_by_id(self, address_id: UUID, user_id: UUID) -> Address:
        """Find an address for a specific user.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): ID of the user owning the address.

        Returns:
            Address: The address with the specified ID.

        Raises:
            HTTPException: If the address does not exists.
        """
        address = await self.uow.addresses.find_user_address(address_id, user_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )
        return address

    async def create(
        self,
        user_id: UUID,
        data: AddressCreate,
    ) -> Address:
        """Create a new address for a user.

        Args:
            user_id (UUID): ID of the user to whom the address belongs.
            data (AddressCreate): The address data to create.

        Returns:
            Address: The created address.

        """
        count = await self.uow.addresses.count(user_id=user_id)
        if count >= MAX_ADDRESSES_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You cannot have more than {MAX_ADDRESSES_PER_USER} addresses.",
            )

        new_address = Address(**data.model_dump(), user_id=user_id)

        return await self.uow.addresses.add(new_address)

    async def update_address(self, address_id: UUID, user_id: UUID, data: AddressUpdate) -> Address:
        """Update an address for a user.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): ID of the user owning the address.
            data (AddressUpdate): The address data to update.

        Returns:
            Address: The updated address.

        Raises:
            HTTPException: If the address does not exists.
        """
        address = await self.uow.addresses.find_user_address(address_id, user_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )

        address_data = data.model_dump(exclude_unset=True)

        for key, value in address_data.items():
            setattr(address, key, value)

        return await self.uow.addresses.update(address)

    async def delete(self, address_id: UUID, user_id: UUID) -> None:
        """Delete an address for a user.

        Args:
            address_id (UUID): Address identifier.
            user_id (UUID): ID of the user owning the address.

        Raises:
            HTTPException: If the address does not exists.
        """
        address = await self.uow.addresses.find_user_address(address_id, user_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )
        await self.uow.addresses.delete(address)

    async def set_default_billing(self, address_id: UUID, user_id: UUID) -> Address:
        """Set an address as the default billing address for a user.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): ID of the user owning the address.

        Returns:
            Address: The updated address.

        Raises:
            HTTPException: If the address does not exists.
        """
        address = await self.uow.addresses.find_user_address(address_id, user_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )

        await self.uow.addresses.unset_default_billing(user_id)

        address.is_default_billing = True

        return await self.uow.addresses.update(address)

    async def set_default_shipping(self, address_id: UUID, user_id: UUID) -> Address:
        """Set an address as the default shipping address for a user.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): ID of the user owning the address.

        Returns:
            Address: The updated address.

        Raises:
            HTTPException: If the address does not exists.
        """
        address = await self.uow.addresses.find_user_address(address_id, user_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )

        await self.uow.addresses.unset_default_shipping(user_id)

        address.is_default_shipping = True

        return await self.uow.addresses.update(address)
