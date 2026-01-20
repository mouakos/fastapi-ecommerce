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
        """Get existing cart or create a new one for user or guest session.

        For authenticated users (user_id provided), finds or creates user cart.
        For guests (session_id provided), finds or creates session-based cart.

        Args:
            user_id (UUID | None): User ID for authenticated users.
            session_id (str | None): Session ID for guest users.

        Returns:
            Cart: Existing or newly created cart.

        Raises:
            ValueError: If session_id is not provided for guest cart.
        """
        ...
