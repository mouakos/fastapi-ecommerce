"""Interface for Cart repository."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.interfaces.generic_repository import GenericRepository
from app.models.cart import Cart, CartItem


class CartRepository(GenericRepository[Cart], ABC):
    """Interface for Cart repository."""

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Cart | None:
        """Get a single cart by user ID.

        Args:
            user_id (UUID): User ID.

        Returns:
            Cart | None: Cart or none.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_by_session_id(self, session_id: str) -> Cart | None:
        """Get a single cart by session ID.

        Args:
            session_id (str): Session ID.

        Returns:
            Cart | None: Cart or none.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_item_by_cart_and_product(
        self, cart_id: UUID, product_id: UUID
    ) -> CartItem | None:
        """Get a single cart item by cart ID and product ID.

        Args:
            cart_id (UUID): Cart ID.
            product_id (UUID): Product ID.

        Returns:
            Cart | None: Cart item or none.
        """
        raise NotImplementedError()

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
        raise NotImplementedError()
