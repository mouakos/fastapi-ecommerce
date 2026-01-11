"""Service module for address-related operations."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate
from app.services.user import UserService


class AddressService:
    """Service class for address-related operations."""

    @staticmethod
    async def list_all(session: AsyncSession, user_id: UUID) -> list[Address]:
        """List all Addresses for a user.

        Args:
            session (AsyncSession): The database session.
            user_id (UUID): The ID of the user.

        Returns:
            list[Address]: A list of all addresses associated to the user.
        """
        stmt = select(Address).where(Address.user_id == user_id)
        result = await session.exec(stmt)
        return list(result.all())

    @staticmethod
    async def get_by_id(session: AsyncSession, address_id: UUID) -> Address:
        """Retrieve a address by its ID.

        Args:
            session (AsyncSession): The database session.
            address_id (UUID): Address ID.

        Raises:
            HTTPException: The ID of the address to retrieve.

        Returns:
            Address: The address with the specified ID.
        """
        address = await session.get(Address, address_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )
        return address

    @staticmethod
    async def create(
        session: AsyncSession,
        data: AddressCreate,
        user_id: UUID,
    ) -> Address:
        """Create a new address for a user.

        Args:
            session (AsyncSession): The database session.
            data (AddressCreate): The address data to create.
            user_id (UUID): The ID of the user to associate the address with.

        Returns:
            Address: The created address.

        Raises:
            HTTPException: If the user does not exists.
        """
        user = await UserService.get_by_id(session, user_id)

        if data.is_default_billing:
            await AddressService._unset_default_billing_address(session, user.id)

        if data.is_default_shipping:
            await AddressService._unset_default_shipping_address(session, user.id)

        address = Address(**data.model_dump(), user_id=user.id)
        session.add(address)
        await session.commit()
        await session.refresh(address)
        return address

    @staticmethod
    async def update(session: AsyncSession, data: AddressUpdate, address_id: UUID) -> Address:
        """Update an address.

        Args:
            session (AsyncSession): The database session.
            data (AddressCreate): The address data to update.
            address_id (UUID): Address ID.

        Returns:
            Address: The updated address.

        Raises:
            HTTPException: If the address does not exists.
        """
        address = await AddressService.get_by_id(session, address_id)

        if data.is_default_billing:
            await AddressService._unset_default_billing_address(session, address.user_id)

        if data.is_default_shipping:
            await AddressService._unset_default_shipping_address(session, address.user_id)

        address_data = data.model_dump(exclude_unset=True)

        for key, value in address_data.items():
            setattr(address, key, value)

        await session.commit()
        await session.refresh(address)
        return address

    @staticmethod
    async def delete(session: AsyncSession, address_id: UUID) -> None:
        """Delete a user address.

        Args:
            session (AsyncSession): Database session.
            address_id (UUID): Address identifier.

        Raises:
            HTTPException: If the address does not exists.
        """
        addr = await AddressService.get_by_id(session, address_id)
        await session.delete(addr)
        await session.commit()

    @staticmethod
    async def _unset_default_shipping_address(session: AsyncSession, user_id: UUID) -> None:
        """Unset an user address as the default shipping address."""
        # unset old default
        stmt = select(Address).where(Address.user_id == user_id, Address.is_default_shipping)
        addresses = (await session.exec(stmt)).all()
        for a in addresses:
            a.is_default_shipping = False
        await session.flush()

    @staticmethod
    async def _unset_default_billing_address(session: AsyncSession, user_id: UUID) -> None:
        """Unset an user address as the default billing address."""
        # unset old default
        stmt = select(Address).where(
            Address.user_id == user_id,
            Address.is_default_billing,
        )
        addresses = (await session.exec(stmt)).all()
        for a in addresses:
            a.is_default_billing = False
        await session.flush()
