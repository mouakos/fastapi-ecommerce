"""Interface for Order repository."""

from abc import ABC

from app.interfaces.generic_repository import GenericRepository
from app.models.order import Order


class OrderRepository(GenericRepository[Order], ABC):
    """Interface for Order repository."""

    pass
