"""SQL Cart repository implementation."""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.cart_repository import CartRepository
from app.models.cart import Cart, CartItem
from app.repositories.sql_generic_repository import SqlGenericRepository


class SqlCartRepository(SqlGenericRepository[Cart], CartRepository):
    """SQL Cart repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, Cart)

    async def find_user_cart(self, user_id: UUID) -> Cart | None:
        """Find a cart by user ID.

        Args:
            user_id (UUID): User ID.

        Returns:
            Cart | None: Cart or none.
        """
        stmt = select(Cart).where(Cart.user_id == user_id)
        result = await self._session.exec(stmt)
        return result.first()

    async def find_session_cart(self, session_id: str) -> Cart | None:
        """Find a cart by session ID.

        Args:
            session_id (str): Session ID.

        Returns:
            Cart | None: Cart or none.
        """
        stmt = select(Cart).where(Cart.session_id == session_id)
        result = await self._session.exec(stmt)
        return result.first()

    async def find_cart_item(self, cart_id: UUID, product_id: UUID) -> CartItem | None:
        """Find a cart item by cart ID and product ID.

        Args:
            cart_id (UUID): Cart ID.
            product_id (UUID): Product ID.

        Returns:
            CartItem | None: Cart item or none.
        """
        stmt = select(CartItem).where(
            (CartItem.cart_id == cart_id) & (CartItem.product_id == product_id)
        )
        result = await self._session.exec(stmt)
        return result.first()

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
        if user_id:
            user_cart = await self.find_user_cart(user_id)
            if user_cart:
                return user_cart

            new_cart = Cart(user_id=user_id)
            await self.add(new_cart)
            return new_cart

        if not session_id:
            raise ValueError("session_id is required for guest cart.")

        guest_cart = await self.find_session_cart(session_id)
        if guest_cart:
            return guest_cart

        new_guest_cart = Cart(session_id=session_id)
        return await self.add(new_guest_cart)
