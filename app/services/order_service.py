"""Order service for handling order-related operations."""

from uuid import UUID

from app.core.exceptions import (
    AddressNotFoundError,
    EmptyCartError,
    InsufficientStockError,
    OrderNotFoundError,
    ProductInactiveError,
)
from app.core.logger import logger
from app.interfaces.unit_of_work import UnitOfWork
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderCreate
from app.utils.order import generate_order_number


class OrderService:
    """Service for managing orders."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def create_order(self, user_id: UUID, data: OrderCreate) -> Order:
        """Create a new order from the user's cart.

        Args:
            user_id (UUID): ID of the user placing the order.
            data (OrderCreate): Order creation data including billing and shipping addresses.

        Returns:
            Order: The created order with PENDING status.

        Raises:
            AddressNotFoundError: If billing or shipping address does not exist.
            EmptyCartError: If the cart is empty.
            InsufficientStockError: If any product is out of stock.
            ProductInactiveError: If any product in the cart is inactive.
        """
        # Validate addresses
        billing_address = await self.uow.addresses.find_user_address(
            data.billing_address_id, user_id
        )
        if not billing_address:
            raise AddressNotFoundError(address_id=data.billing_address_id, user_id=user_id)

        shipping_address = await self.uow.addresses.find_user_address(
            data.shipping_address_id, user_id
        )
        if not shipping_address:
            raise AddressNotFoundError(address_id=data.shipping_address_id, user_id=user_id)

        # Validate cart
        cart = await self.uow.carts.get_or_create(user_id=user_id, session_id=None)
        if not cart.items:
            raise EmptyCartError(cart_id=cart.id)

        # Validate stock
        for item in cart.items:
            if not item.product.is_active:
                raise ProductInactiveError(product_id=item.product_id)

            if item.quantity > item.product.stock:
                raise InsufficientStockError(
                    product_id=item.product_id,
                    requested=item.quantity,
                    available=item.product.stock,
                )

        total_amount = sum(item.unit_price * item.quantity for item in cart.items)

        new_order = Order(
            user_id=user_id,
            billing_address_id=data.billing_address_id,
            shipping_address_id=data.shipping_address_id,
            total_amount=total_amount,
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

            # TODO: Reduce stock after payment confirmation
            item.product.stock -= item.quantity
            await self.uow.products.update(item.product)

        # Clear cart
        await self.uow.carts.delete(cart)

        updated_order = await self.uow.orders.update(created_order)
        logger.info(
            "order_created",
            order_id=str(updated_order.id),
            user_id=str(user_id),
            order_number=updated_order.order_number,
            total_amount=float(total_amount),
        )
        return updated_order

    async def get_order(self, order_id: UUID, user_id: UUID) -> Order:
        """Get an order for a specific user.

        Args:
            order_id (UUID): The ID of the order.
            user_id (UUID): The ID of the user.

        Returns:
            Order: The order data.

        Raises:
            OrderNotFoundError: If the order is not found.
        """
        order = await self.uow.orders.find_user_order(order_id, user_id)
        if not order:
            raise OrderNotFoundError(order_id=order_id, user_id=user_id)
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
        return await self.uow.orders.find_all(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
        )
