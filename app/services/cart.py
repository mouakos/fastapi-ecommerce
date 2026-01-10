"""Service layer for Category operations."""

from uuid import UUID

from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.schemas.cart import CartItemCreate, CartItemUpdate
from app.services.product import ProductService


class CartService:
    """Service layer for Category operations."""

    @staticmethod
    async def get_or_create_cart(
        session: AsyncSession, user_id: UUID | None, session_id: str | None
    ) -> Cart:
        """Get or create a cart for a user.

        Args:
            session (AsyncSession): Database session.
            user_id (UUID | None): User ID.
            session_id (str | None): Session ID.

        Returns:
            Cart: Existing or new cart.

        Raises:
            HTTPException: If session_id is not provided for guest cart.
        """
        if user_id:
            user_cart = await CartService._get_cart_by_user_id(session, user_id)
            if not user_cart:
                user_cart = Cart(user_id=user_id)
                session.add(user_cart)
                await session.flush()
                await session.refresh(user_cart)

            if session_id:
                guest_cart = await CartService._get_cart_by_session_id(session, session_id)
                if guest_cart:
                    await CartService._merge_carts(session, user_cart, guest_cart)
                    await session.delete(guest_cart)

            await session.commit()
            await session.refresh(user_cart)
            return user_cart

        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required for guest cart.")

        guest_cart = await CartService._get_cart_by_session_id(session, session_id)
        if guest_cart:
            return guest_cart

        guest_cart = Cart(session_id=session_id)
        session.add(guest_cart)
        await session.commit()
        await session.refresh(guest_cart)
        return guest_cart

    @staticmethod
    async def add_item(
        session: AsyncSession, data: CartItemCreate, session_id: str | None, user_id: UUID | None
    ) -> Cart:
        """Add an item to the cart.

        Args:
            session (AsyncSession): Database session.
            data (CartItemCreate): Data for the cart item.
            session_id (UUID | None): Session ID.
            user_id (UUID | None): User ID.

        Returns:
            Cart: Updated cart instance.

        Raises:
            HTTPException: If the product is out of stock or not available.
        """
        cart = await CartService.get_or_create_cart(session, user_id, session_id)

        product = await ProductService.get_by_id(session, data.product_id)

        if not product.is_published:
            raise HTTPException(status_code=400, detail="Product is not available.")

        existing_item = (
            await session.exec(
                select(CartItem).where(
                    CartItem.cart_id == cart.id, CartItem.product_id == product.id
                )
            )
        ).first()

        current_qty = existing_item.quantity if existing_item else 0
        new_qty = current_qty + data.quantity

        if product.stock < new_qty:
            raise HTTPException(status_code=400, detail="Product out of stock.")

        if existing_item:
            existing_item.quantity += data.quantity
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

        await session.commit()
        await session.refresh(cart)
        return cart

    @staticmethod
    async def update_item(
        session: AsyncSession,
        product_id: UUID,
        data: CartItemUpdate,
        session_id: str | None,
        user_id: UUID | None,
    ) -> Cart:
        """Update the quantity of an item in the cart.

        Args:
            session (AsyncSession): Database session.
            product_id (UUID): Product ID.
            data (CartItemUpdate): Data for updating the cart item.
            session_id (str | None): Session ID.
            user_id (UUID | None): User ID.

        Returns:
            Cart: Updated cart instance.

        Raises:
            HTTPException: If product is not found in cart, out of stock, or not available.
        """
        cart = await CartService.get_or_create_cart(session, user_id, session_id)

        item = (
            await session.exec(
                select(CartItem).where(
                    CartItem.cart_id == cart.id, CartItem.product_id == product_id
                )
            )
        ).first()
        if not item:
            raise HTTPException(status_code=404, detail="Product not found in cart.")

        product = await ProductService.get_by_id(session, item.product_id)

        if not product.is_published:
            raise HTTPException(status_code=400, detail="Product is not available.")

        if product.stock < data.quantity:
            raise HTTPException(status_code=400, detail="Product out of stock.")

        item.quantity = data.quantity

        await session.commit()
        await session.refresh(cart)
        return cart

    @staticmethod
    async def remove_item(
        session: AsyncSession, product_id: UUID, session_id: str | None, user_id: UUID | None
    ) -> Cart:
        """Remove an item from the cart.

        Args:
            session (AsyncSession): Database session.
            product_id (UUID): Product ID.
            session_id (str | None): Session ID.
            user_id (UUID | None): User ID.

        Returns:
            Cart: Updated cart instance.

        Raises:
            HTTPException: If product is not found in cart.
        """
        cart = await CartService.get_or_create_cart(session, user_id, session_id)

        item = (
            await session.exec(
                select(CartItem).where(
                    CartItem.cart_id == cart.id, CartItem.product_id == product_id
                )
            )
        ).first()

        if not item:
            raise HTTPException(status_code=404, detail="Product not found in cart.")

        await session.delete(item)
        await session.commit()
        await session.refresh(cart)
        return cart

    @staticmethod
    async def _get_cart_by_user_id(session: AsyncSession, user_id: UUID) -> Cart | None:
        """Get the cart for a specific user.

        Args:
            session (AsyncSession): Database session.
            user_id (UUID): User ID.

        Returns:
            Cart | None: User cart or None.
        """
        return (await session.exec(select(Cart).where(Cart.user_id == user_id))).first()

    @staticmethod
    async def _get_cart_by_session_id(session: AsyncSession, session_id: str) -> Cart | None:
        """Get the cart for a specific session.

        Args:
            session (AsyncSession): Database session.
            session_id (str): Session ID.

        Returns:
            Cart | None: Session cart or None.
        """
        return (await session.exec(select(Cart).where(Cart.session_id == session_id))).first()

    @staticmethod
    async def _merge_carts(session: AsyncSession, user_cart: Cart, guest_cart: Cart) -> None:
        """Merge session cart into user cart.

        Args:
            session (AsyncSession): Database session.
            user_cart (Cart): User's cart.
            guest_cart (Cart): Session's cart.
        """
        for item in guest_cart.items:
            existing_item = next(
                (ci for ci in user_cart.items if ci.product_id == item.product_id), None
            )
            if existing_item:
                existing_item.quantity += item.quantity
            else:
                session.add(
                    CartItem(
                        cart_id=user_cart.id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        product_name=item.product_name,
                        product_image_url=item.product_image_url,
                    )
                )

        await session.flush()
        await session.refresh(user_cart)
