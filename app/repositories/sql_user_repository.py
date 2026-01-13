"""SQL User repository implementation."""

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.user_repository import UserRepository
from app.models.user import User
from app.repositories.sql_generic_repository import SqlGenericRepository


class SqlUserRepository(SqlGenericRepository[User], UserRepository):
    """SQL User repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        """Get a single user by email.

        Args:
            email (str): User email.

        Returns:
            User | None: User or none.
        """
        stmt = select(User).where(User.email == email)
        result = await self._session.exec(stmt)
        return result.first()
