"""Service for managing wishlist items."""

from uuid import UUID

from fastapi import HTTPException

from app.interfaces.unit_of_work import UnitOfWork
from app.models.cart import Cart, CartItem
from app.models.wishlist_item import WishlistItem
from app.schemas.wishlist_schema import (
    WishlistActionRead,
    WishlistItemRead,
    WishlistRead,
    WishlistStatsRead,
)


class WishlistService:
    """Service for managing wishlist items."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a wishlist repository."""
        self.uow = uow

    async def add_item(self, user_id: UUID, product_id: UUID) -> WishlistActionRead:
        """Add a product to the user's wishlist.

        Args:
            user_id (UUID): User ID.
            product_id (UUID): Product ID.
        """
        product = await self.uow.products.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        wishlist_item = await self.uow.wishlists.get_by_user_and_product(user_id, product_id)
        if not wishlist_item:
            new_wishlist_item = WishlistItem(user_id=user_id, product_id=product_id)
            await self.uow.wishlists.add(new_wishlist_item)
            return WishlistActionRead(
                message="Product added to wishlist.",
                product_id=product_id,
            )
        return WishlistActionRead(
            message="Product already in wishlist.",
            product_id=product_id,
        )

    async def get_items(self, user_id: UUID) -> WishlistRead:
        """Get all wishlist items for a user.

        Args:
            user_id (UUID): User ID.

        Returns:
            WishlistRead: Wishlist items.

        """
        wishlist_items = await self.uow.wishlists.get_by_user_id(user_id)

        wishlist_read_items = []
        for wishlist_item in wishlist_items:
            wishlist_read_items.append(
                WishlistItemRead(
                    id=wishlist_item.id,
                    product_id=wishlist_item.product_id,
                    product_name=wishlist_item.product.name,
                    product_price=wishlist_item.product.price,
                    product_image_url=wishlist_item.product.image_url,
                    product_slug=wishlist_item.product.slug,
                    product_stock_quantity=wishlist_item.product.stock,
                    product_is_published=wishlist_item.product.is_published,
                    added_at=wishlist_item.created_at,
                )
            )

        return WishlistRead(
            items=wishlist_read_items,
            total_items=len(wishlist_read_items),
        )

    async def remove_item(self, user_id: UUID, product_id: UUID) -> WishlistActionRead:
        """Remove a product from the user's wishlist.

        Args:
            user_id (UUID): User ID.
            product_id (UUID): Product ID.

        Returns:
            WishlistActionRead: Action result.
        """
        wishlist_item = await self.uow.wishlists.get_by_user_and_product(user_id, product_id)
        if not wishlist_item:
            raise HTTPException(status_code=404, detail="Product not found in wishlist.")

        await self.uow.wishlists.delete(wishlist_item.id)

        return WishlistActionRead(
            message="Product removed from wishlist successfully.",
            product_id=product_id,
        )

    async def clear(self, user_id: UUID) -> WishlistActionRead:
        """Clear all wishlist items for a user.

        Args:
            user_id (UUID): User ID.

        Returns:
            WishlistActionRead: Action result.
        """
        await self.uow.wishlists.delete_by_user_id(user_id)
        return WishlistActionRead(
            message="Wishlist cleared successfully.",
            product_id=None,
        )

    async def get_count(self, user_id: UUID) -> WishlistStatsRead:
        """Get the count of wishlist items for a user.

        Args:
            user_id (UUID): User ID.

        Returns:
            WishlistStatsRead: Wishlist statistics.
        """
        count = await self.uow.wishlists.count_by_user_id(user_id)
        return WishlistStatsRead(count=count)

    async def move_to_cart(self, user_id: UUID, product_id: UUID) -> WishlistActionRead:
        """Move a product from the wishlist to the cart.

        Args:
            user_id (UUID): User ID.
            product_id (UUID): Product ID.

        Returns:
            WishlistActionRead: Action result.
        """
        product = await self.uow.products.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        if not product.is_published:
            raise HTTPException(status_code=400, detail="Product is not available")

        if product.stock < 1:
            raise HTTPException(status_code=400, detail="Product out of stock.")

        wishlist_item = await self.uow.wishlists.get_by_user_and_product(user_id, product_id)
        if not wishlist_item:
            raise HTTPException(status_code=404, detail="Product not found in wishlist.")

        # Add to cart
        user_cart = await self.uow.carts.get_by_user_id(user_id)
        if not user_cart:
            user_cart = Cart(user_id=user_id)
            await self.uow.carts.add(user_cart)

        cart_item = await self.uow.carts.get_item_by_cart_and_product(user_cart.id, product_id)
        if cart_item:
            cart_item.quantity += 1
        else:
            new_cart_item = CartItem(
                cart_id=user_cart.id,
                product_id=product_id,
                quantity=1,
                product_name=product.name,
                product_image_url=product.image_url,
                unit_price=product.price,
            )
            user_cart.items.append(new_cart_item)

        await self.uow.carts.update(user_cart)

        # Remove from wishlist
        await self.uow.wishlists.delete(wishlist_item.id)

        return WishlistActionRead(
            message="Product moved to cart successfully.",
            product_id=product_id,
        )
