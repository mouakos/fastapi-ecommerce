"""Service module for address-related operations."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import HTTPException, status

from app.interfaces.unit_of_work import UnitOfWork
from app.models.address import Address
from app.schemas.address import AddressCreate, AddressRead, AddressUpdate

MAX_ADDRESSES_PER_USER = 10


class AddressService:
    """Service class for address-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def get_user_addresses(self, user_id: UUID) -> list[AddressRead]:
        """List all Addresses for a user.

        Args:
            user_id (UUID): User ID to filter addresses.

        Returns:
            list[AddressRead]: List of addresses associated with the user.

        Raises:
            HTTPException: If the user does not exist.
        """
        user = await self.uow.users.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return await self.uow.addresses.list_all(user_id=user_id)

    async def get_user_address(self, address_id: UUID, user_id: UUID) -> AddressRead:
        """Retrieve an address for a specific user.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): User ID.

        Returns:
            AddressRead: The address with the specified ID.

        Raises:
            HTTPException: If the address does not exists.
        """
        address = await self.uow.addresses.get_for_user(address_id, user_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )
        return address

    async def create_user_address(
        self,
        user_id: UUID,
        data: AddressCreate,
    ) -> AddressRead:
        """Create a new address for a user.

        Args:
            user_id (UUID): User ID.
            data (AddressCreate): The address data to create.

        Returns:
            AddressRead: The created address.

        Raises:
            HTTPException: If the user does not exist.
        """
        user = await self.uow.users.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        count = await self.uow.addresses.count_all(user_id=user_id)
        if count >= MAX_ADDRESSES_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User cannot have more than {MAX_ADDRESSES_PER_USER} addresses.",
            )

        new_address = Address(**data.model_dump(), user_id=user_id)

        return await self.uow.addresses.add(new_address)

    async def update_user_address(
        self, address_id: UUID, user_id: UUID, data: AddressUpdate
    ) -> AddressRead:
        """Update an address for a user.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): User ID.
            data (AddressUpdate): The address data to update.

        Returns:
            AddressRead: The updated address.

        Raises:
            HTTPException: If the address does not exists.
        """
        address = await self.uow.addresses.get_for_user(address_id, user_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )

        address_data = data.model_dump(exclude_unset=True)

        for key, value in address_data.items():
            setattr(address, key, value)

        return await self.uow.addresses.update(address)

    async def delete_user_address(self, address_id: UUID, user_id: UUID) -> None:
        """Delete an address for a user.

        Args:
            address_id (UUID): Address identifier.
            user_id (UUID): User ID.

        Raises:
            HTTPException: If the address does not exists.
        """
        address = await self.uow.addresses.get_for_user(address_id, user_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )
        await self.uow.addresses.delete_by_id(address.id)

    async def set_user_default_billing_address(
        self, address_id: UUID, user_id: UUID
    ) -> AddressRead:
        """Set an address as the default billing address for a user.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): User ID.

        Returns:
            AddressRead: The updated address.

        Raises:
            HTTPException: If the address does not exists.
        """
        address = await self.uow.addresses.get_for_user(address_id, user_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )

        await self.uow.addresses.unset_default_billing_for_user(user_id)

        address.is_default_billing = True

        return await self.uow.addresses.update(address)

    async def set_user_default_shipping_address(
        self, address_id: UUID, user_id: UUID
    ) -> AddressRead:
        """Set an address as the default shipping address for a user.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): User ID.

        Returns:
            AddressRead: The updated address.

        Raises:
            HTTPException: If the address does not exists.
        """
        address = await self.uow.addresses.get_for_user(address_id, user_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )

        await self.uow.addresses.unset_default_shipping_for_user(user_id)

        address.is_default_shipping = True

        return await self.uow.addresses.update(address)
