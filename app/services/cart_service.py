"""Service layer for cart operations."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import HTTPException

from app.interfaces.unit_of_work import UnitOfWork
from app.models.cart import Cart, CartItem
from app.schemas.cart_schema import CartItemCreate, CartItemUpdate, CartRead


class CartService:
    """Service layer for cart operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def get_or_create(self, user_id: UUID | None, session_id: str | None) -> CartRead:
        """Get or create a cart for a user.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.

        Returns:
            CartRead: Existing or new cart.

        Raises:
            HTTPException: If session_id is not provided for guest cart.
        """
        return await self._get_or_create(user_id, session_id)

    async def add_item(
        self, user_id: UUID | None, session_id: str | None, data: CartItemCreate
    ) -> CartRead:
        """Add an item to the cart.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.
            data (CartItemCreate): Data for the cart item.

        Returns:
            CartRead: Updated cart instance.

        Raises:
            HTTPException: If the product is out of stock or not available.
        """
        cart = await self._get_or_create(user_id, session_id)

        product = await self.uow.products.get_by_id(data.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        if not product.is_active:
            raise HTTPException(status_code=400, detail="Product is not available.")

        item = await self.uow.carts.get_item_by_cart_and_product(cart.id, product.id)

        current_qty = item.quantity if item else 0
        new_qty = current_qty + data.quantity

        if product.stock < new_qty:
            raise HTTPException(status_code=400, detail="Product out of stock.")

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

    async def update_item(
        self,
        user_id: UUID | None,
        session_id: str | None,
        product_id: UUID,
        data: CartItemUpdate,
    ) -> CartRead:
        """Update the quantity of an item in the cart.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.
            product_id (UUID): Product ID.
            data (CartItemUpdate): Data for updating the cart item.

        Returns:
            CartRead: Updated cart instance.

        Raises:
            HTTPException: If product is not found in cart, out of stock, or not available.
        """
        cart = await self._get_or_create(user_id, session_id)

        item = await self.uow.carts.get_item_by_cart_and_product(cart.id, product_id)
        if not item:
            raise HTTPException(status_code=404, detail="Product not found in cart.")

        product = await self.uow.products.get_by_id(item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        if not product.is_active:
            raise HTTPException(status_code=400, detail="Product is not available.")

        if product.stock < data.quantity:
            raise HTTPException(status_code=400, detail="Product out of stock.")

        item.quantity = data.quantity

        return await self.uow.carts.update(cart)

    async def remove_item(
        self, user_id: UUID | None, session_id: str | None, product_id: UUID
    ) -> CartRead:
        """Remove an item from the cart.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.
            product_id (UUID): Product ID.

        Returns:
            CartRead: Updated cart instance.

        Raises:
            HTTPException: If product is not found in cart.
        """
        cart = await self._get_or_create(user_id, session_id)

        item = await self.uow.carts.get_item_by_cart_and_product(cart.id, product_id)

        if not item:
            raise HTTPException(status_code=404, detail="Product not found in cart.")

        cart.items.remove(item)
        return await self.uow.carts.update(cart)

    async def _get_or_create(self, user_id: UUID | None, session_id: str | None) -> Cart:
        """Get or create a cart for a user.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.

        Returns:
            CartRead: Existing or new cart.

        Raises:
            HTTPException: If session_id is not provided for guest cart.
        """
        """Get or create cart via repository."""
        try:
            return await self.uow.carts.get_or_create(user_id, session_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    async def clear(self, user_id: UUID | None, session_id: str | None) -> CartRead:
        """Clear all items from the cart.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.

        Returns:
            CartRead: Updated cart instance with no items.
        """
        cart = await self._get_or_create(user_id, session_id)
        cart.items.clear()
        return await self.uow.carts.update(cart)

    async def merge_carts(self, user_id: UUID, session_id: str) -> None:
        """Merge carts associated with a user ID and a session ID into the user's cart and delete the guest cart.

        Args:
            user_id (UUID): User ID.
            session_id (str): Session ID.
        """
        guest_cart = await self.uow.carts.get_by_session_id(session_id)

        if not guest_cart:
            return

        user_cart = await self._get_or_create(user_id, None)

        for item in guest_cart.items:
            existing_item = await self.uow.carts.get_item_by_cart_and_product(
                user_cart.id, item.product_id
            )
            if existing_item:
                existing_item.quantity += item.quantity
            else:
                guest_cart.items.remove(item)
                item.cart_id = user_cart.id
                user_cart.items.append(item)

        await self.uow.carts.update(user_cart)
        await self.uow.carts.delete_by_id(guest_cart.id)
