"""SQL User repository implementation."""

from uuid import UUID

from sqlmodel import delete, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.wishlist_repository import WishlistRepository
from app.models.wishlist_item import WishlistItem
from app.repositories.sql_generic_repository import SqlGenericRepository


class SqlWishlistRepository(SqlGenericRepository[WishlistItem], WishlistRepository):
    """SQL User repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, WishlistItem)

    async def find_by_user_id(self, user_id: UUID) -> list[WishlistItem]:
        """Get all wishlist items by user ID.

        Args:
            user_id (UUID): User ID.

        Returns:
            list[WishlistItem]: List of wishlist items.
        """
        stmt = select(WishlistItem).where(WishlistItem.user_id == user_id)
        result = await self._session.exec(stmt)
        return list(result.all())

    async def find_by_user_and_product(
        self, user_id: UUID, product_id: UUID
    ) -> WishlistItem | None:
        """Get a wishlist item by user ID and product ID.

        Args:
            user_id (UUID): User ID.
            product_id (UUID): Product ID.

        Returns:
            Wishlist | None: Wishlist item or none.
        """
        stmt = select(WishlistItem).where(
            (WishlistItem.user_id == user_id) & (WishlistItem.product_id == product_id)
        )
        result = await self._session.exec(stmt)
        return result.first()

    async def delete_by_user_id(self, user_id: UUID) -> None:
        """Clear all wishlist items for a user.

        Args:
            user_id (UUID): User ID.
        """
        stmt = delete(WishlistItem).where(WishlistItem.user_id == user_id)  # type: ignore  [arg-type]
        await self._session.exec(stmt)
        await self._session.flush()

    async def count(self, user_id: UUID) -> int:
        """Get the count of wishlist items for a user.

        Args:
            user_id (UUID): User ID.

        Returns:
            int: Count of wishlist items.
        """
        stmt = select(func.count()).select_from(WishlistItem).where(WishlistItem.user_id == user_id)
        result = await self._session.exec(stmt)
        return result.first() or 0
