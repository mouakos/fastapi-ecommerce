"""Interface for Wishlist repository."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.wishlist_item import WishlistItem


class WishlistRepository(GenericRepository[WishlistItem], ABC):
    """Interface for Wishlist repository."""

    @abstractmethod
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
