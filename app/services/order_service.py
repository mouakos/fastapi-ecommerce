"""Order service for handling order-related operations."""

from decimal import Decimal
from uuid import UUID

import ulid

from app.core.exceptions import (
    AddressNotFoundError,
    EmptyCartError,
    InsufficientStockError,
    OrderNotFoundError,
    ProductInactiveError,
)
from app.core.logger import logger
from app.interfaces.unit_of_work import UnitOfWork
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderAddress, OrderAddressKind, OrderItem, OrderStatus
from app.schemas.order import OrderCreate


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
        billing_address = await self._get_user_addresses(data.billing_address_id, user_id)
        shipping_address = await self._get_user_addresses(data.shipping_address_id, user_id)

        # Validate cart
        cart = await self.uow.carts.get_or_create(user_id=user_id, session_id=None)
        self._validate_cart_items(cart)

        # Calculate total amount
        subtotal = sum(item.unit_price * item.quantity for item in cart.items)
        tax_amount = subtotal * Decimal("0.07")  # Example: 7% tax
        shipping_amount = Decimal("5.00")  # Example: flat shipping rate
        total_amount = subtotal + tax_amount + shipping_amount

        new_order = Order(
            user_id=user_id,
            total_amount=total_amount,
            order_number=self._generate_order_number(),
            tax_amount=tax_amount,
            shipping_amount=shipping_amount,
        )
        created_order = await self.uow.orders.add(new_order)

        # Snapshot shipping/billing addresses for historical accuracy
        shipping_address_snapshot = self.create_order_address_snapshot(
            created_order.id, shipping_address, OrderAddressKind.SHIPPING
        )
        billing_address_snapshot = self.create_order_address_snapshot(
            created_order.id, billing_address, OrderAddressKind.BILLING
        )
        new_order.addresses.append(shipping_address_snapshot)
        new_order.addresses.append(billing_address_snapshot)

        # Create order items
        order_items = self._create_order_items(cart.items)
        created_order.items.extend(order_items)

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

    def create_order_address_snapshot(
        self,
        order_id: UUID,
        address: Address,
        address_kind: OrderAddressKind,
    ) -> OrderAddress:
        """Create a snapshot of an order address.

        Args:
            order_id (UUID): The ID of the order.
            address (Address): The address to snapshot.
            address_kind (OrderAddressKind): The kind of address (BILLING or SHIPPING).

        Returns:
            OrderAddress: The created order address snapshot.
        """
        return OrderAddress(
            order_id=order_id,
            kind=address_kind,
            line1=address.line1,
            line2=address.line2,
            city=address.city,
            state=address.state,
            postal_code=address.postal_code,
            country=address.country,
            full_name=address.full_name,
            phone_number=address.phone_number,
        )

    async def _get_user_addresses(self, address_id: UUID, user_id: UUID) -> Address:
        """Get user addresses.

        Args:
            address_id (UUID): Address ID.
            user_id (UUID): User ID.

        Returns:
            Address: The address data.

        Raises:
            AddressNotFoundError: If the address is not found.
        """
        address = await self.uow.addresses.find_user_address(address_id, user_id)
        if not address:
            raise AddressNotFoundError(address_id=address_id, user_id=user_id)
        return address

    def _validate_cart_items(self, cart: Cart) -> None:
        """Validate cart items for stock and product status.

        Args:
            cart (Cart): The user's cart.

        Raises:
            EmptyCartError: If the cart is empty.
            InsufficientStockError: If any product is out of stock.
            ProductInactiveError: If any product in the cart is inactive.
        """
        if not cart.items:
            raise EmptyCartError(cart_id=cart.id)

        for item in cart.items:
            if not item.product.is_active:
                raise ProductInactiveError(product_id=item.product_id)

            if item.quantity > item.product.stock:
                raise InsufficientStockError(
                    product_id=item.product_id,
                    requested=item.quantity,
                    available=item.product.stock,
                )

    def _create_order_items(self, cart_items: list[CartItem]) -> list[OrderItem]:
        """Create order items from cart items.

        Args:
            cart_items (list[CartItem]): List of cart items.

        Returns:
            list[OrderItem]: List of order items.
        """
        order_items = []
        for item in cart_items:
            order_item = OrderItem(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                product_name=item.product_name,
                product_image_url=item.product_image_url,
            )
            order_items.append(order_item)
        return order_items

    def _generate_order_number(self) -> str:
        """Generate a unique order number."""
        return f"ORD-{ulid.new().str}"
