"""Service module for address-related operations."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import HTTPException, status

from app.interfaces.unit_of_work import UnitOfWork
from app.models.address import Address
from app.schemas.address_schema import AddressCreate, AddressRead, AddressUpdate


class AddressService:
    """Service class for address-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def list_all(self, user_id: UUID) -> list[AddressRead]:
        """List all Addresses for a user.

        Args:
            user_id (UUID): The ID of the user.

        Returns:
            list[AddressRead]: A list of all addresses associated to the user.
        """
        return await self.uow.addresses.list_all(user_id=user_id)

    async def get_by_id(self, address_id: UUID) -> AddressRead:
        """Retrieve a address by its ID.

        Args:
            address_id (UUID): Address ID.

        Raises:
            HTTPException: The ID of the address to retrieve.

        Returns:
            AddressRead: The address with the specified ID.
        """
        address = await self.uow.addresses.get_by_id(address_id)
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
    ) -> AddressRead:
        """Create a new address for a user.

        Args:
            user_id (UUID): The ID of the user to associate the address with.
            data (AddressCreate): The address data to create.

        Returns:
            AddressRead: The created address.

        Raises:
            HTTPException: If the user does not exists.
        """
        user = await self.uow.users.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if data.is_default_billing:
            await self.uow.addresses.unset_user_default_billing_address(user.id)

        if data.is_default_shipping:
            await self.uow.addresses.unset_user_default_shipping_address(user.id)

        new_address = Address(**data.model_dump(), user_id=user.id)

        return await self.uow.addresses.add(new_address)

    async def update(self, address_id: UUID, data: AddressUpdate) -> AddressRead:
        """Update an address.

        Args:
            address_id (UUID): Address ID.
            data (AddressUpdate): The address data to update.

        Returns:
            AddressRead: The updated address.

        Raises:
            HTTPException: If the address does not exists.
        """
        address = await self.uow.addresses.get_by_id(address_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )

        if data.is_default_billing:
            await self.uow.addresses.unset_user_default_billing_address(address.user_id)

        if data.is_default_shipping:
            await self.uow.addresses.unset_user_default_shipping_address(address.user_id)

        address_data = data.model_dump(exclude_unset=True)

        for key, value in address_data.items():
            setattr(address, key, value)

        return await self.uow.addresses.update(address)

    async def delete(self, address_id: UUID) -> None:
        """Delete a user address.

        Args:
            address_id (UUID): Address identifier.

        Raises:
            HTTPException: If the address does not exists.
        """
        address = await self.get_by_id(address_id)
        await self.uow.addresses.delete(address.id)
