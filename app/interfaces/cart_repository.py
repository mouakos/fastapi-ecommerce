"""Interface for Cart repository."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.cart import Cart, CartItem


class CartRepository(GenericRepository[Cart], ABC):
    """Interface for Cart repository."""

    @abstractmethod
    async def find_user_cart(self, user_id: UUID) -> Cart | None:
        """Find a cart by user ID.

        Args:
            user_id (UUID): User ID.

        Returns:
            Cart | None: Cart or none.
        """
        ...

    @abstractmethod
    async def find_session_cart(self, session_id: str) -> Cart | None:
        """Find a cart by session ID.

        Args:
            session_id (str): Session ID.

        Returns:
            Cart | None: Cart or none.
        """
        ...

    @abstractmethod
    async def find_cart_item(self, cart_id: UUID, product_id: UUID) -> CartItem | None:
        """Find a cart item by cart ID and product ID.

        Args:
            cart_id (UUID): Cart ID.
            product_id (UUID): Product ID.

        Returns:
            CartItem | None: Cart item or none.
        """
        ...

    @abstractmethod
    async def get_or_create(self, user_id: UUID | None, session_id: str | None) -> Cart:
        """Get or create a cart for a user.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.

        Returns:
            Cart: Existing or new cart.

        Raises:
            ValueError: If session_id is not provided for guest cart.
        """
        ...
