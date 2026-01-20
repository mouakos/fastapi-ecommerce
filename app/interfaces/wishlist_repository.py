"""Interface for Wishlist repository."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.wishlist_item import WishlistItem


class WishlistRepository(GenericRepository[WishlistItem], ABC):
    """Interface for Wishlist repository."""

    @abstractmethod
    async def paginate(
        self,
        *,
        user_id: UUID,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[WishlistItem], int]:
        """Paginate wishlist items by user ID.

        Args:
            user_id (UUID): User ID.
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of items per page. Defaults to 10.

        Returns:
            tuple[list[WishlistItem], int]: List of wishlist items and total count.
        """
        ...

    @abstractmethod
    async def find_item(self, user_id: UUID, product_id: UUID) -> WishlistItem | None:
        """Find a wishlist item by user ID and product ID.

        Args:
            user_id (UUID): User ID.
            product_id (UUID): Product ID.

        Returns:
            WishlistItem | None: Wishlist item or none.

        """
        ...

    @abstractmethod
    async def delete_by_user_id(self, user_id: UUID) -> None:
        """Delete all wishlist items for a user.

        Args:
            user_id (UUID): User ID.
        """
        ...
