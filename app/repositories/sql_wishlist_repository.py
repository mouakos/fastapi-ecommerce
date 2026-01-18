"""SQL Wishlist repository implementation."""

from uuid import UUID

from sqlmodel import delete, desc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.wishlist_repository import WishlistRepository
from app.models.wishlist_item import WishlistItem
from app.repositories.sql_generic_repository import SqlGenericRepository


class SqlWishlistRepository(SqlGenericRepository[WishlistItem], WishlistRepository):
    """SQL Wishlist repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, WishlistItem)

    async def list_by_user_id(
        self, user_id: UUID, page: int, page_size: int
    ) -> tuple[list[WishlistItem], int]:
        """List all wishlist items by user ID.

        Args:
            user_id (UUID): User ID.
            page (int): Page number.
            page_size (int): Number of items per page.

        Returns:
            tuple[list[WishlistItem], int]: List of wishlist items and total count.
        """
        stmt = select(WishlistItem).where(WishlistItem.user_id == user_id)

        total_result = await self._session.exec(select(func.count()).select_from(stmt.subquery()))
        total = total_result.first() or 0

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        stmt = stmt.order_by(desc(WishlistItem.created_at))
        result = await self._session.exec(stmt)
        items = list(result.all())
        return items, total

    async def find_item(self, user_id: UUID, product_id: UUID) -> WishlistItem | None:
        """Find a wishlist item by user ID and product ID.

        Args:
            user_id (UUID): User ID.
            product_id (UUID): Product ID.

        Returns:
            WishlistItem | None: Wishlist item or none.
        """
        stmt = select(WishlistItem).where(
            (WishlistItem.user_id == user_id) & (WishlistItem.product_id == product_id)
        )
        result = await self._session.exec(stmt)
        return result.first()

    async def delete_by_user_id(self, user_id: UUID) -> None:
        """Delete all wishlist items for a user.

        Args:
            user_id (UUID): User ID.
        """
        stmt = delete(WishlistItem).where(WishlistItem.user_id == user_id)  # type: ignore  [arg-type]
        await self._session.exec(stmt)
        await self._session.flush()
