"""Service layer for cart operations."""

# mypy: disable-error-code=return-value
from uuid import UUID

from app.core.exceptions import (
    InsufficientStockError,
    InvalidCartSessionError,
    ProductInactiveError,
    ProductNotFoundError,
    ProductNotInCartError,
)
from app.interfaces.unit_of_work import UnitOfWork
from app.models.cart import Cart, CartItem
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartRead


class CartService:
    """Service layer for cart operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def get_or_create_cart(self, user_id: UUID | None, session_id: str | None) -> CartRead:
        """Get or create a cart for a user.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.

        Returns:
            CartRead: Existing or new cart.

        Raises:
            InvalidCartSessionError: If session_id is not provided for guest cart.
        """
        return await self._get_or_create_cart(user_id, session_id)

    async def add_cart_item(
        self, user_id: UUID | None, session_id: str | None, data: CartItemCreate
    ) -> Cart:
        """Add a product to the cart or increment quantity if already exists.

        Args:
            user_id (UUID | None): ID of authenticated user, or None for guest.
            session_id (str | None): Session ID for guest cart.
            data (CartItemCreate): Product ID and quantity to add.

        Returns:
            Cart: Updated cart with added item.

        Raises:
            ProductNotFoundError: If product does not exist.
            ProductInactiveError: If product is not active.
            InsufficientStockError: If insufficient stock available.
        """
        cart = await self._get_or_create_cart(user_id, session_id)

        product = await self.uow.products.find_by_id(data.product_id)
        if not product:
            raise ProductNotFoundError(product_id=data.product_id)

        if not product.is_active:
            raise ProductInactiveError(product_name=product.name)

        item = await self.uow.carts.find_cart_item(cart.id, product.id)

        current_qty = item.quantity if item else 0
        new_qty = current_qty + data.quantity

        if product.stock < new_qty:
            raise InsufficientStockError(
                product_name=product.name, requested=new_qty, available=product.stock
            )

        if item:
            item.quantity += data.quantity
        else:
            new_item = CartItem(
                cart_id=cart.id,
                product_id=product.id,
                quantity=data.quantity,
                unit_price=product.price,
                product_name=product.name,
                product_image_url=product.image_url,
            )
            cart.items.append(new_item)

        return await self.uow.carts.update(cart)

    async def update_cart_item(
        self,
        user_id: UUID | None,
        session_id: str | None,
        product_id: UUID,
        data: CartItemUpdate,
    ) -> Cart:
        """Update the quantity of an item in the cart.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.
            product_id (UUID): Product ID.
            data (CartItemUpdate): Data for updating the cart item.

        Returns:
            Cart: Updated cart instance.

        Raises:
            ProductNotFoundError: If product does not exist.
            ProductNotInCartError: If product is not in the cart.
            ProductInactiveError: If product is not active.
            InsufficientStockError: If insufficient stock available.
        """
        product = await self.uow.products.find_by_id(product_id)
        if not product:
            raise ProductNotFoundError(product_id=product_id)

        cart = await self._get_or_create_cart(user_id, session_id)

        item = await self.uow.carts.find_cart_item(cart.id, product_id)
        if not item:
            raise ProductNotInCartError(product_id=product_id)

        if not product.is_active:
            raise ProductInactiveError(product_name=product.name)

        if product.stock < data.quantity:
            raise InsufficientStockError(
                product_name=product.name, requested=data.quantity, available=product.stock
            )

        item.quantity = data.quantity

        return await self.uow.carts.update(cart)

    async def remove_cart_item(
        self, user_id: UUID | None, session_id: str | None, product_id: UUID
    ) -> Cart:
        """Remove an item from the cart.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.
            product_id (UUID): Product ID.

        Returns:
            Cart: Updated cart instance.

        Raises:
            ProductNotInCartError: If product is not in the cart.
        """
        cart = await self._get_or_create_cart(user_id, session_id)

        item = await self.uow.carts.find_cart_item(cart.id, product_id)

        if not item:
            raise ProductNotInCartError(product_id=product_id)

        cart.items.remove(item)
        return await self.uow.carts.update(cart)

    async def _get_or_create_cart(self, user_id: UUID | None, session_id: str | None) -> Cart:
        """Get or create a cart for a user.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.

        Returns:
            CartRead: Existing or new cart.

        Raises:
            InvalidCartSessionError: If session_id is not provided for guest cart.
        """
        """Get or create cart via repository."""
        try:
            return await self.uow.carts.get_or_create(user_id, session_id)
        except ValueError as e:
            raise InvalidCartSessionError(message=str(e)) from e

    async def clear_cart_items(self, user_id: UUID | None, session_id: str | None) -> CartRead:
        """Clear all items from the cart.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.

        Returns:
            CartRead: Updated cart instance with no items.
        """
        cart = await self._get_or_create_cart(user_id, session_id)
        cart.items.clear()
        return await self.uow.carts.update(cart)

    async def merge_carts(self, user_id: UUID, session_id: str) -> None:
        """Merge guest cart into user cart after authentication.

        Combines quantities for matching products and deletes the guest cart.

        Args:
            user_id (UUID): ID of the authenticated user.
            session_id (str): Session ID of the guest cart to merge.
        """
        guest_cart = await self.uow.carts.find_session_cart(session_id)

        if not guest_cart:
            return

        user_cart = await self._get_or_create_cart(user_id, None)

        for item in guest_cart.items:
            existing_item = await self.uow.carts.find_cart_item(user_cart.id, item.product_id)
            if existing_item:
                existing_item.quantity += item.quantity
            else:
                guest_cart.items.remove(item)
                item.cart_id = user_cart.id
                user_cart.items.append(item)

        await self.uow.carts.update(user_cart)
        await self.uow.carts.delete(guest_cart)
