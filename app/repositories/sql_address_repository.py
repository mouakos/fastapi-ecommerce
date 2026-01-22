"""SQL Address repository implementation."""

from uuid import UUID

from sqlalchemy import update
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

    async def find_user_address(self, address_id: UUID, user_id: UUID) -> Address | None:
        """Find an address by ID with user ownership validation.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): User ID for ownership validation.

        Returns:
            Address | None: The address if found and owned by user, otherwise None.
        """
        stmt = select(Address).where((Address.id == address_id) & (Address.user_id == user_id))
        result = await self._session.exec(stmt)
        return result.first()

    async def unset_default_billing(self, user_id: UUID) -> None:
        """Unset the default billing address for a user.

        Args:
            user_id (UUID): ID of the user owning the address.
        """
        stmt = (
            update(Address)
            .where((Address.user_id == user_id) & (Address.is_default_billing.is_(True)))  # type: ignore [attr-defined]
            .values(is_default_billing=False)
        )
        await self._session.exec(stmt)

    async def unset_default_shipping(self, user_id: UUID) -> None:
        """Unset the default shipping address for a user.

        Args:
            user_id (UUID): ID of the user owning the address.
        """
        stmt = (
            update(Address)
            .where((Address.user_id == user_id) & (Address.is_default_shipping.is_(True)))  # type: ignore [attr-defined]
            .values(is_default_shipping=False)
        )
        await self._session.exec(stmt)
