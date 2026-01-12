"""SQLModel Unit of Work implementation."""

from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.unit_of_work import UnitOfWork
from app.repositories.sql_address_repository import SqlAddressRepository
from app.repositories.sql_cart_repository import SqlCartRepository
from app.repositories.sql_category_repository import SqlCategoryRepository
from app.repositories.sql_product_repository import SqlProductRepository
from app.repositories.sql_user_repository import SqlUserRepository


class SqlModelUnitOfWork(UnitOfWork):
    """SQLModel Unit of Work implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Creates a new uow instance.

        Args:
            session (AsyncSession): Database session.
        """
        self._session = session

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self._session.rollback()

    def _init_repositories(self) -> None:
        self.addresses = SqlAddressRepository(self._session)
        self.carts = SqlCartRepository(self._session)
        self.categories = SqlCategoryRepository(self._session)
        self.products = SqlProductRepository(self._session)
        self.users = SqlUserRepository(self._session)
