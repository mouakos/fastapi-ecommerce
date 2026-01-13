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

    async def unset_user_default_shipping_address(self, user_id: UUID) -> None:
        """Unset the default shipping address for a user.

        Args:
            user_id (UUID): The ID of the user.
        """
        stmt = select(Address).where(Address.user_id == user_id, Address.is_default_shipping)
        addresses = (await self._session.exec(stmt)).all()
        for a in addresses:
            a.is_default_shipping = False
        await self._session.flush()

    async def unset_user_default_billing_address(self, user_id: UUID) -> None:
        """Unset the default billing address for a user.

        Args:
            user_id (UUID): The ID of the user.
        """
        stmt = select(Address).where(Address.user_id == user_id, Address.is_default_billing)
        addresses = (await self._session.exec(stmt)).all()
        for a in addresses:
            a.is_default_billing = False
        await self._session.flush()
