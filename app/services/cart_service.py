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
from app.core.logger import logger
from app.interfaces.unit_of_work import UnitOfWork
from app.models.cart import Cart, CartItem


class CartService:
    """Service layer for cart operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def get_cart(self, user_id: UUID | None, session_id: str | None) -> Cart:
        """Get the current user's cart or session cart.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.

        Returns:
            Cart: User's cart or session cart.

        Raises:
            InvalidCartSessionError: If session_id is not provided for guest cart.
        """
        return await self._get_or_create_cart(user_id, session_id)

    async def add_product_to_cart(
        self,
        *,
        product_id: UUID,
        quantity: int,
        user_id: UUID | None,
        session_id: str | None,
    ) -> None:
        """Add a product to the cart or increment quantity if already exists.

        Args:
            user_id (UUID | None): ID of authenticated user, or None for guest.
            session_id (str | None): Session ID for guest cart.
            product_id (UUID): Product ID to add.
            quantity (int): Quantity to add.

        Raises:
            ProductNotFoundError: If product does not exist.
            ProductInactiveError: If product is not active.
            InsufficientStockError: If insufficient stock available.
        """
        cart = await self._get_or_create_cart(user_id, session_id)

        product = await self.uow.products.find_by_id(product_id)
        if not product:
            raise ProductNotFoundError(product_id=product_id)
        if not product.is_active:
            raise ProductInactiveError(product_id=product.id)

        item = await self.uow.carts.find_cart_item(cart.id, product.id)

        current_qty = item.quantity if item else 0
        new_qty = current_qty + quantity

        if product.stock < new_qty:
            raise InsufficientStockError(
                product_id=product.id, requested=new_qty, available=product.stock
            )

        if item:
            item.quantity += quantity
        else:
            new_item = CartItem(
                cart_id=cart.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price,
                product_name=product.name,
                product_image_url=product.image_url,
            )
            cart.items.append(new_item)
            logger.info(
                "product_added_to_cart",
                cart_id=str(cart.id),
                product_id=str(product.id),
                quantity=quantity,
            )

        await self.uow.carts.update(cart)

    async def update_product_quantity(
        self,
        *,
        product_id: UUID,
        quantity: int,
        user_id: UUID | None,
        session_id: str | None,
    ) -> None:
        """Update the quantity of an item in the cart.

        If quantity is set to zero, the item is removed from the cart.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.
            product_id (UUID): Product ID.
            quantity (int): Quantity for updating the cart item.

        Raises:
            ProductNotFoundError: If product does not exist.
            ProductNotInCartError: If product is not in the cart.
            InsufficientStockError: If insufficient stock available.
        """
        product = await self.uow.products.find_by_id(product_id)
        if not product:
            raise ProductNotFoundError(product_id=product_id)

        if not product.is_active:
            raise ProductInactiveError(product_id=product.id)

        cart = await self._get_or_create_cart(user_id, session_id)

        item = await self.uow.carts.find_cart_item(cart.id, product_id)
        if not item:
            raise ProductNotInCartError(product_id=product_id, cart_id=cart.id)

        if quantity == 0:
            cart.items.remove(item)
            await self.uow.carts.update(cart)
            return

        if product.stock < quantity:
            raise InsufficientStockError(
                product_id=product.id, requested=quantity, available=product.stock
            )

        item.quantity = quantity

        await self.uow.carts.update(cart)

    async def remove_product_from_cart(
        self, user_id: UUID | None, session_id: str | None, product_id: UUID
    ) -> None:
        """Remove an item from the cart.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.
            product_id (UUID): Product ID.

        Raises:
            ProductNotInCartError: If product is not in the cart.
        """
        cart = await self._get_or_create_cart(user_id, session_id)

        item = await self.uow.carts.find_cart_item(cart.id, product_id)

        if not item:
            raise ProductNotInCartError(product_id=product_id, cart_id=cart.id)

        cart.items.remove(item)
        await self.uow.carts.update(cart)
        logger.info(
            "product_removed_from_cart",
            cart_id=str(cart.id),
            product_id=str(product_id),
        )

    async def _get_or_create_cart(self, user_id: UUID | None, session_id: str | None) -> Cart:
        """Get or create a cart for a user.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.

        Returns:
            Cart: Existing or new cart.

        Raises:
            InvalidCartSessionError: If session_id is not provided for guest cart.
        """
        try:
            return await self.uow.carts.get_or_create(user_id, session_id)
        except ValueError as e:
            raise InvalidCartSessionError(message=str(e)) from e

    async def clear_cart(self, user_id: UUID | None, session_id: str | None) -> None:
        """Clear all items from the cart.

        Args:
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.
        """
        cart = await self._get_or_create_cart(user_id, session_id)
        cart.items.clear()
        await self.uow.carts.update(cart)
        logger.info("cart_cleared", cart_id=str(cart.id))

    async def merge_carts(self, user_id: UUID, session_id: str) -> None:
        """Merge guest cart into user cart after authentication.

        Combines quantities for matching products and deletes the guest cart.
        If a product is inactive or out of stock, it is dropped from the merge.
        If merged quantity exceeds stock, it is capped at available stock.

        Args:
            user_id (UUID): ID of the authenticated user.
            session_id (str): Session ID of the guest cart to merge.
        """
        guest_cart = await self.uow.carts.find_session_cart(session_id)

        if not guest_cart:
            return

        user_cart = await self._get_or_create_cart(user_id, None)

        # Iterate over a copy since we may move items between carts.
        for item in list(guest_cart.items):
            product = item.product

            if not product.is_active:
                logger.info(
                    "cart_merge_item_dropped_product_inactive", product_id=str(item.product_id)
                )
                continue

            if product.stock <= 0:
                logger.info("cart_merge_item_dropped_out_of_stock", product_id=str(item.product_id))
                continue

            existing_item = await self.uow.carts.find_cart_item(user_cart.id, item.product_id)
            if existing_item:
                merged_qty = existing_item.quantity + item.quantity
                capped_qty = min(merged_qty, product.stock)
                if capped_qty != merged_qty:
                    logger.info(
                        "cart_merge_quantity_capped",
                        product_id=str(item.product_id),
                        requested=merged_qty,
                        applied=capped_qty,
                        available=product.stock,
                    )
                existing_item.quantity = capped_qty
            else:
                if item.quantity > product.stock:
                    logger.info(
                        "cart_merge_quantity_capped",
                        product_id=str(item.product_id),
                        requested=item.quantity,
                        applied=product.stock,
                        available=product.stock,
                    )
                    item.quantity = product.stock
                user_cart.items.append(item)

        await self.uow.carts.update(user_cart)
        await self.uow.carts.delete(guest_cart)
        logger.info("carts_merged", cart_id=str(user_cart.id))
