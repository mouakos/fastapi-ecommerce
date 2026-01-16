"""Interface for Wishlist repository."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.wishlist_item import WishlistItem


class WishlistRepository(GenericRepository[WishlistItem], ABC):
    """Interface for Wishlist repository."""

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> list[WishlistItem]:
        """Get all wishlist items by user ID.

        Args:
            user_id (UUID): User ID.

        Returns:
            list[Wishlist]: List of wishlist items.
        """
        ...

    @abstractmethod
    async def get_by_user_and_product(self, user_id: UUID, product_id: UUID) -> WishlistItem | None:
        """Get a wishlist item by user ID and product ID.

        Args:
            user_id (UUID): User ID.
            product_id (UUID): Product ID.

        Returns:
            Wishlist | None: Wishlist item or none.

        """
        ...

    @abstractmethod
    async def delete_by_user_id(self, user_id: UUID) -> None:
        """Clear all wishlist items for a user.

        Args:
            user_id (UUID): User ID.
        """
        ...

    @abstractmethod
    async def count_by_user_id(self, user_id: UUID) -> int:
        """Get the count of wishlist items for a user.

        Args:
            user_id (UUID): User ID.

        Returns:
            int: Count of wishlist items.
        """
        ...
