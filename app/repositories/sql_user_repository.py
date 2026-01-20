"""SQL User repository implementation."""

from datetime import timedelta

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.user_repository import UserRepository
from app.models.user import User, UserRole
from app.repositories.sql_generic_repository import SqlGenericRepository
from app.utils.utc_time import utcnow


class SqlUserRepository(SqlGenericRepository[User], UserRepository):
    """SQL User repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, User)

    async def find_by_email(self, email: str) -> User | None:
        """Find a user by email.

        Args:
            email (str): User email.

        Returns:
            User | None: User or none.
        """
        stmt = select(User).where(User.email == email)
        result = await self._session.exec(stmt)
        return result.first()

    async def count_recent(self, days: int) -> int:
        """Get number of users registered in the last N days.

        Args:
            days (int): Number of days to look back from today.

        Returns:
            int: Number of users registered in the last N days.
        """
        cutoff_date = utcnow() - timedelta(days=days)
        stmt = select(func.count()).select_from(User).where(User.created_at >= cutoff_date)
        result = await self._session.exec(stmt)
        return result.first() or 0

    async def paginate(
        self,
        *,
        role: UserRole | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[User], int]:
        """Get all users with pagination and optional filters.

        Args:
            role (UserRole | None, optional): Filter by user role. Defaults to None.
            search (str | None, optional): Search query for email. Defaults to None.
            sort_by (str, optional): Field to sort by. Defaults to "created_at".
            sort_order (str, optional): Sort order, either "asc" or "desc". Defaults to "desc".
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 10.

        Returns:
            tuple[list[User], int]: List of users and total count.
        """
        stmt = select(User)

        # Apply role filter
        if role is not None:
            stmt = stmt.where(User.role == role)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(User.email.ilike(search_pattern))  # type: ignore [attr-defined]

        # Apply sorting
        sort_columns = {
            "created_at": User.created_at,
            "email": User.email,
            "role": User.role,
        }.get(sort_by, User.created_at)
        sort_column = sort_columns.desc() if sort_order == "desc" else sort_columns.asc()  # type: ignore [attr-defined]
        stmt = stmt.order_by(sort_column)

        # Get total count
        count_result = await self._session.exec(stmt)
        total = len(count_result.all())

        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        # Execute query
        result = await self._session.exec(stmt)
        users = list(result.all())

        return users, total
