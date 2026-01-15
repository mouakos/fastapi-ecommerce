"""Service module for address-related operations."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import HTTPException, status

from app.interfaces.unit_of_work import UnitOfWork
from app.models.address import Address
from app.models.user import UserRole
from app.schemas.address import AddressCreate, AddressRead, AddressUpdate
from app.schemas.user import UserRead


class AddressService:
    """Service class for address-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def list_all(
        self, current_user: UserRead, user_id: UUID | None = None
    ) -> list[AddressRead]:
        """List all Addresses for a user.

        If user_id is not provided, lists addresses for the current user.

        Args:
            current_user (UserRead): Current user information.
            user_id (UUID | None): User ID to filter addresses.

        Returns:
            list[AddressRead]: List of addresses associated with the user.
        """
        target_user_id = user_id or current_user.id

        if current_user.id != target_user_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these addresses.",
            )
        return await self.uow.addresses.list_all(user_id=target_user_id)

    async def get_by_id(self, current_user: UserRead, address_id: UUID) -> AddressRead:
        """Retrieve a address by its ID.

        Args:
            current_user (UserRead): Current user information.
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
        if address.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this address.",
            )
        return address

    async def create(
        self,
        current_user: UserRead,
        data: AddressCreate,
    ) -> AddressRead:
        """Create a new address for a user.

        Args:
            current_user (UserRead): Current user information.
            data (AddressCreate): The address data to create.

        Returns:
            AddressRead: The created address.
        """
        await self._unset_default(current_user.id, data)

        new_address = Address(**data.model_dump(), user_id=current_user.id)

        return await self.uow.addresses.add(new_address)

    async def update(
        self, current_user: UserRead, address_id: UUID, data: AddressUpdate
    ) -> AddressRead:
        """Update an address.

        Args:
            current_user (UserRead): Current user information.
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

        if address.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this address.",
            )

        await self._unset_default(current_user.id, data)

        address_data = data.model_dump(exclude_unset=True)

        for key, value in address_data.items():
            setattr(address, key, value)

        return await self.uow.addresses.update(address)

    async def delete(self, current_user: UserRead, address_id: UUID) -> None:
        """Delete a user address.

        Args:
            current_user (UserRead): Current user information.
            address_id (UUID): Address identifier.

        Raises:
            HTTPException: If the address does not exists.
        """
        address = await self.uow.addresses.get_by_id(address_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )
        if address.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this address.",
            )
        await self.uow.addresses.delete_by_id(address.id)

    async def _unset_default(self, user_id: UUID, data: AddressCreate | AddressUpdate) -> None:
        """Unset default address if needed.

        Args:
            user_id (UUID): User ID.
            data (AddressCreate | AddressUpdate): Address data.
        """
        if data.is_default_billing:
            await self.uow.addresses.unset_default(user_id, "billing")

        if data.is_default_shipping:
            await self.uow.addresses.unset_default(user_id, "shipping")
