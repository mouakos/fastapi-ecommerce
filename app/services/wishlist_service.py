"""Service for managing wishlist items."""

from uuid import UUID

from app.core.exceptions import (
    DuplicateWishlistItemError,
    InsufficientStockError,
    ProductInactiveError,
    ProductNotFoundError,
    ProductNotInWishlistError,
)
from app.core.logger import logger
from app.interfaces.unit_of_work import UnitOfWork
from app.models.cart import Cart, CartItem
from app.models.wishlist_item import WishlistItem


class WishlistService:
    """Service for managing wishlist items."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a wishlist repository."""
        self.uow = uow

    async def add_product_to_wishlist(self, user_id: UUID, product_id: UUID) -> None:
        """Add a product to the user's wishlist.

        If the product is already in the wishlist, it will not be added again.

        Args:
            user_id (UUID): ID of the user.
            product_id (UUID): ID of the product to add.

        Raises:
            ProductNotFoundError: If the product does not exist.
        """
        product = await self.uow.products.find_by_id(product_id)
        if not product:
            raise ProductNotFoundError(product_id=product_id)

        wishlist_item = await self.uow.wishlists.find_item(user_id, product.id)
        if wishlist_item:
            raise DuplicateWishlistItemError(product_id=product_id, user_id=user_id)

        new_wishlist_item = WishlistItem(user_id=user_id, product_id=product.id)
        logger.info("product_added_to_wishlist", user_id=str(user_id), product_id=str(product.id))
        await self.uow.wishlists.add(new_wishlist_item)

    async def get_wishlist_items(
        self, user_id: UUID, page: int = 1, page_size: int = 10
    ) -> tuple[list[WishlistItem], int]:
        """List all wishlist items for a user.

        Args:
            user_id (UUID): User ID.
            page (int): Page number.
            page_size (int): Number of items per page.

        Returns:
            tuple[list[WishlistItem], int]: Wishlist items and total count.
        """
        return await self.uow.wishlists.find_all(page=page, page_size=page_size, user_id=user_id)

    async def remove_product_from_wishlist(self, user_id: UUID, product_id: UUID) -> None:
        """Remove a product from the user's wishlist.

        Args:
            user_id (UUID): User ID.
            product_id (UUID): Product ID.

        Raises:
            ProductNotInWishlistError: If product is not in wishlist.
        """
        wishlist_item = await self.uow.wishlists.find_item(user_id, product_id)
        if not wishlist_item:
            raise ProductNotInWishlistError(product_id=product_id, user_id=user_id)

        await self.uow.wishlists.delete(wishlist_item)
        logger.info(
            "product_removed_from_wishlist", user_id=str(user_id), product_id=str(product_id)
        )

    async def clear_wishlist(self, user_id: UUID) -> None:
        """Clear all wishlist items for a user.

        Args:
            user_id (UUID): User ID.
        """
        count = await self.uow.wishlists.delete_by_user_id(user_id)
        logger.info("wishlist_cleared", user_id=str(user_id), deleted_count=count)

    async def get_wishlist_item_count(self, user_id: UUID) -> int:
        """Get the total number of wishlist items for a user.

        Args:
            user_id (UUID): User ID.

        Returns:
            int: Wishlist item count.
        """
        return await self.uow.wishlists.count(user_id=user_id)

    async def add_product_from_wishlist_to_cart(self, user_id: UUID, product_id: UUID) -> None:
        """Add a product from wishlist to cart.

        Adds product to cart with quantity of 1, or increments quantity if already in cart.

        Args:
            user_id (UUID): ID of the user.
            product_id (UUID): ID of the product to add.

        Raises:
            ProductNotInWishlistError: If product is not in wishlist.
            ProductInactiveError: If product is inactive.
            InsufficientStockError: If product is out of stock.
        """
        wishlist_item = await self.uow.wishlists.find_item(user_id, product_id)
        if not wishlist_item:
            raise ProductNotInWishlistError(product_id=product_id, user_id=user_id)

        # Check product availability
        if not wishlist_item.product.is_active:
            raise ProductInactiveError(product_id=product_id)

        # Check stock
        if wishlist_item.product.stock < 1:
            raise InsufficientStockError(
                product_id=product_id,
                requested=1,
                available=wishlist_item.product.stock,
            )

        # Add to cart
        user_cart = await self.uow.carts.find_user_cart(user_id)
        if not user_cart:
            user_cart = Cart(user_id=user_id)
            await self.uow.carts.add(user_cart)

        # Check if item already in cart
        cart_item = await self.uow.carts.find_cart_item(user_cart.id, product_id)
        if cart_item:
            cart_item.quantity += 1
        else:
            new_cart_item = CartItem(
                cart_id=user_cart.id,
                product_id=product_id,
                quantity=1,
                product_name=wishlist_item.product.name,
                product_image_url=wishlist_item.product.image_url,
                unit_price=wishlist_item.product.price,
            )
            user_cart.items.append(new_cart_item)

        await self.uow.carts.update(user_cart)
        logger.info(
            "product_added_from_wishlist_to_cart",
            user_id=str(user_id),
            product_id=str(product_id),
            cart_id=str(user_cart.id),
        )
