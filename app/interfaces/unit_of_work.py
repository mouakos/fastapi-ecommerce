"""Abstract base class for Unit of Work pattern."""

from abc import ABC, abstractmethod
from types import TracebackType

from app.interfaces.address_repository import AddressRepository
from app.interfaces.cart_repository import CartRepository
from app.interfaces.category_repository import CategoryRepository
from app.interfaces.order_repository import OrderRepository
from app.interfaces.payment_repository import PaymentRepository
from app.interfaces.product_repository import ProductRepository
from app.interfaces.user_repository import UserRepository
from app.interfaces.wishlist_repository import WishlistRepository


class UnitOfWork(ABC):
    """Abstract base class for Unit of Work pattern."""

    carts: CartRepository
    products: ProductRepository
    categories: CategoryRepository
    users: UserRepository
    addresses: AddressRepository
    orders: OrderRepository
    wishlists: WishlistRepository
    payments: PaymentRepository

    async def __aenter__(self) -> "UnitOfWork":
        """Enter the runtime context related to this object."""
        self._init_repositories()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Exit the runtime context related to this object."""
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
        return False

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        pass

    @abstractmethod
    def _init_repositories(self) -> None:
        """Initialize repositories."""
        pass
