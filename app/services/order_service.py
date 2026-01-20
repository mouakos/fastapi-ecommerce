"""Order service for handling order-related operations."""

from uuid import UUID

from fastapi import HTTPException

from app.interfaces.unit_of_work import UnitOfWork
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderCreate
from app.utils.order_utils import generate_order_number


class OrderService:
    """Service for managing orders."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def create_order(self, user_id: UUID, data: OrderCreate) -> Order:
        """Create a new order for the user."""
        # Validate addresses
        billing_address = await self.uow.addresses.find_by_id(data.billing_address_id)
        if not billing_address or billing_address.user_id != user_id:
            raise HTTPException(status_code=400, detail="Invalid billing address.")

        shipping_address = await self.uow.addresses.find_by_id(data.shipping_address_id)
        if not shipping_address or shipping_address.user_id != user_id:
            raise HTTPException(status_code=400, detail="Invalid shipping address.")

        # Validate cart
        cart = await self.uow.carts.find_user_cart(user_id)
        if not cart or not cart.items:
            raise HTTPException(status_code=400, detail="Cart is empty.")

        # Validate stock
        for item in cart.items:
            if item.quantity > item.product.stock:
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
            order_number=generate_order_number(),
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
        await self.uow.carts.delete(cart)

        return await self.uow.orders.update(created_order)

    async def get_order(self, order_id: UUID, user_id: UUID) -> Order:
        """Get an order for a specific user.

        Args:
            order_id (UUID): The ID of the order.
            user_id (UUID): The ID of the user.

        Returns:
            Order: The order data.

        Raises:
            HTTPException: If the order is not found.
        """
        order = await self.uow.orders.find_user_order(order_id, user_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found.")
        return order

    async def get_orders(
        self,
        *,
        user_id: UUID,
        status: OrderStatus | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Order], int]:
        """Get all orders for a user.

        Args:
            user_id (UUID): The ID of the user.
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of orders per page. Defaults to 10.
            status (OrderStatus | None, optional): Filter by order status. Defaults to None.
            sort_by (str, optional): Field to sort by. Defaults to "created_at".
            sort_order (str, optional): Sort order ("asc" or "desc"). Defaults to "desc".

        Returns:
            tuple[list[Order], int]: List of orders for the user and total count.
        """
        return await self.uow.orders.paginate(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
        )
