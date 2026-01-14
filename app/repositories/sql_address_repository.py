"""SQL Address repository implementation."""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.address_repository import AddressRepository, AddressType
from app.models.address import Address
from app.repositories.sql_generic_repository import SqlGenericRepository


class SqlAddressRepository(SqlGenericRepository[Address], AddressRepository):
    """SQL Address repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, Address)

    async def unset_default(self, user_id: UUID, address_type: AddressType) -> None:
        """Unset the default address for a user and address type.

        Args:
            user_id (UUID): User ID.
            address_type (AddressType): Address type (shipping or billing).

        Raises:
            ValueError: If the address type is invalid.
        """
        stmt = select(Address).where(Address.user_id == user_id)

        if address_type == "shipping":
            stmt = stmt.where(Address.is_default_shipping)
        elif address_type == "billing":
            stmt = stmt.where(Address.is_default_billing)
        else:
            raise ValueError("Invalid address type")
        result = await self._session.exec(stmt)
        addresses = result.all()
        for address in addresses:
            if address_type == "shipping":
                address.is_default_shipping = False
            elif address_type == "billing":
                address.is_default_billing = False
            self._session.add(address)
        await self._session.flush()
