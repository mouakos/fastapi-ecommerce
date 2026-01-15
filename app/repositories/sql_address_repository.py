"""SQL Address repository implementation."""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.address_repository import AddressRepository
from app.models.address import Address
from app.repositories.sql_generic_repository import SqlGenericRepository


class SqlAddressRepository(SqlGenericRepository[Address], AddressRepository):
    """SQL Address repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, Address)

    async def get_for_user(self, address_id: UUID, user_id: UUID) -> Address | None:
        """Get a single address for a user.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): User ID.

        Returns:
            Address | None: The address if found, otherwise None.
        """
        stmt = select(Address).where((Address.id == address_id) & (Address.user_id == user_id))
        result = await self._session.exec(stmt)
        return result.first()

    async def unset_default_billing_for_user(self, user_id: UUID) -> None:
        """Unset the default billing address for a user.

        Args:
            user_id (UUID): User ID.
        """
        stmt = select(Address).where((Address.user_id == user_id) & (Address.is_default_billing))
        result = await self._session.exec(stmt)
        address = result.first()
        if address:
            address.is_default_billing = False
            self._session.add(address)
            await self._session.flush()

    async def unset_default_shipping_for_user(self, user_id: UUID) -> None:
        """Unset the default shipping address for a user.

        Args:
            user_id (UUID): User ID.
        """
        stmt = select(Address).where((Address.user_id == user_id) & (Address.is_default_shipping))
        result = await self._session.exec(stmt)
        address = result.first()
        if address:
            address.is_default_shipping = False
            self._session.add(address)
            await self._session.flush()
