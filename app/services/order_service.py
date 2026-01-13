"""Order service for handling order-related operations."""

# mypy: disable-error-code=return-value
from uuid import UUID

import ulid
from fastapi import HTTPException

from app.interfaces.unit_of_work import UnitOfWork
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order_schema import OrderCreate, OrderRead


class OrderService:
    """Service for managing orders."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def checkout(self, user_id: UUID, data: OrderCreate) -> OrderRead:
        """Create a new order for the user."""
        # Validate addresses
        billing_address = await self.uow.addresses.get_by_id(data.billing_address_id)
        if not billing_address or billing_address.user_id != user_id:
            raise HTTPException(status_code=400, detail="Invalid billing address.")

        shipping_address = await self.uow.addresses.get_by_id(data.shipping_address_id)
        if not shipping_address or shipping_address.user_id != user_id:
            raise HTTPException(status_code=400, detail="Invalid shipping address.")

        # Validate cart
        cart = await self.uow.carts.get_by_user_id(user_id)
        if not cart or not cart.items:
            raise HTTPException(status_code=400, detail="Cart is empty.")

        # Validate stock
        for item in cart.items:
            product = await self.uow.products.get_by_id(item.product_id)
            if not product or item.quantity > product.stock:
                raise HTTPException(
                    status_code=400,
                    detail=f"{item.product_name} out of stock.",
                )

        total_amount = sum(item.unit_price * item.quantity for item in cart.items)

        new_order = Order(
            user_id=user_id,
            billing_address_id=data.billing_address_id,
            shipping_address_id=data.shipping_address_id,
            total_amount=total_amount,
            status=OrderStatus.PENDING,
            payment_status=OrderStatus.PENDING,
            order_number=self._order_number(),
        )
        created_order = await self.uow.orders.add(new_order)

        # Create order items + reduce stock
        for item in cart.items:
            order_item = OrderItem(
                order_id=created_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                product_name=item.product_name,
                product_image_url=item.product_image_url,
            )
            created_order.items.append(order_item)

            # Reduce stock
            item.product.stock -= item.quantity
            await self.uow.products.update(item.product)

        # Clear cart
        await self.uow.carts.delete(cart.id)

        return await self.uow.orders.update(created_order)

    async def get_by_id(self, order_id: UUID) -> OrderRead:
        """Get an order by its ID.

        Args:
            order_id (UUID): The ID of the order.

        Returns:
            OrderRead: The order data.

        Raises:
            HTTPException: If the order is not found.
        """
        order = await self.uow.orders.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found.")
        return order

    async def list_all(self, user_id: UUID) -> list[OrderRead]:
        """List all orders for a user.

        Args:
            user_id (UUID): The ID of the user.

        Returns:
            list[OrderRead]: List of orders for the user.
        """
        return await self.uow.orders.list_all(user_id=user_id)

    def _order_number(self) -> str:
        return f"ORD-{ulid.new().str}"
