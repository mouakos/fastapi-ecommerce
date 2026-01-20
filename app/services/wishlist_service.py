"""Service for managing wishlist items."""

from uuid import UUID

from fastapi import HTTPException

from app.interfaces.unit_of_work import UnitOfWork
from app.models.cart import Cart, CartItem
from app.models.wishlist_item import WishlistItem


class WishlistService:
    """Service for managing wishlist items."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a wishlist repository."""
        self.uow = uow

    async def add_wishlist_item(self, user_id: UUID, product_id: UUID) -> None:
        """Add a product to the user's wishlist.

        Args:
            user_id (UUID): User ID.
            product_id (UUID): Product ID.
        """
        product = await self.uow.products.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        wishlist_item = await self.uow.wishlists.find_item(user_id, product_id)
        if not wishlist_item:
            new_wishlist_item = WishlistItem(user_id=user_id, product_id=product_id)
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
        return await self.uow.wishlists.paginate(page=page, page_size=page_size, user_id=user_id)

    async def remove_wishlist_item(self, user_id: UUID, product_id: UUID) -> None:
        """Remove a product from the user's wishlist.

        Args:
            user_id (UUID): User ID.
            product_id (UUID): Product ID.
        """
        wishlist_item = await self.uow.wishlists.find_item(user_id, product_id)
        if not wishlist_item:
            raise HTTPException(status_code=404, detail="Product not found in wishlist.")

        await self.uow.wishlists.delete(wishlist_item)

    async def clear_wishlist_items(self, user_id: UUID) -> None:
        """Clear all wishlist items for a user.

        Args:
            user_id (UUID): User ID.
        """
        await self.uow.wishlists.delete_by_user_id(user_id)

    async def get_wishlist_item_count(self, user_id: UUID) -> int:
        """Get the total number of wishlist items for a user.

        Args:
            user_id (UUID): User ID.

        Returns:
            int: Wishlist item count.
        """
        return await self.uow.wishlists.count(user_id=user_id)

    async def move_wishlist_item_to_cart(self, user_id: UUID, product_id: UUID) -> None:
        """Move a product from the wishlist to the cart.

        Args:
            user_id (UUID): User ID.
            product_id (UUID): Product ID.
        """
        product = await self.uow.products.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        if not product.is_active:
            raise HTTPException(status_code=400, detail="Product is no longer available")

        if product.stock < 1:
            raise HTTPException(status_code=400, detail="Product out of stock.")

        wishlist_item = await self.uow.wishlists.find_item(user_id, product_id)
        if not wishlist_item:
            raise HTTPException(status_code=404, detail="Product not found in wishlist.")

        # Add to cart
        user_cart = await self.uow.carts.find_user_cart(user_id)
        if not user_cart:
            user_cart = Cart(user_id=user_id)
            await self.uow.carts.add(user_cart)

        cart_item = await self.uow.carts.find_cart_item(user_cart.id, product_id)
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
        await self.uow.wishlists.delete(wishlist_item)
