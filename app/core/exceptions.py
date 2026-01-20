"""Custom exceptions for the application."""

from typing import Any
from uuid import UUID


class AppError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the AppError."""
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


# ============= Resource Not Found Exceptions ============= #


class NotFoundError(AppError):
    """Base exception for not found errors."""

    def __init__(
        self,
        resource: str,
        identifier: UUID | str | None = None,
        message: str | None = None,
    ) -> None:
        """Initialize NotFoundError."""
        msg = message or f"{resource} not found."
        details = {"resource": resource}
        if identifier:
            details["identifier"] = str(identifier)
        super().__init__(
            message=msg,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details=details,
        )


class UserNotFoundError(NotFoundError):
    """User not found exception."""

    def __init__(self, user_id: UUID | None = None) -> None:
        """Initialize UserNotFoundError."""
        super().__init__(resource="User", identifier=user_id)


class ProductNotFoundError(NotFoundError):
    """Product not found exception."""

    def __init__(self, product_id: UUID | None = None, slug: str | None = None) -> None:
        """Initialize ProductNotFoundError."""
        identifier = product_id if product_id else slug
        super().__init__(resource="Product", identifier=identifier)
        # Add slug to details if provided (when looking up by slug)
        if slug and not product_id:
            self.details["slug"] = slug


class OrderNotFoundError(NotFoundError):
    """Order not found exception."""

    def __init__(self, order_id: UUID | None = None, user_id: UUID | None = None) -> None:
        """Initialize OrderNotFoundError."""
        super().__init__(resource="Order", identifier=order_id)
        # Add user_id to details if provided
        if user_id:
            self.details["user_id"] = str(user_id)


class ReviewNotFoundError(NotFoundError):
    """Review not found exception."""

    def __init__(self, *, review_id: UUID | None = None, user_id: UUID | None = None) -> None:
        """Initialize ReviewNotFoundError."""
        super().__init__(resource="Review", identifier=review_id)
        # Add user_id to details if provided
        if user_id:
            self.details["user_id"] = str(user_id)


class PaymentNotFoundError(NotFoundError):
    """Payment not found exception."""

    def __init__(self, session_id: str | None = None) -> None:
        """Initialize PaymentNotFoundError."""
        super().__init__(resource="Payment", identifier=session_id)
        if session_id:
            self.details["session_id"] = session_id


class AddressNotFoundError(NotFoundError):
    """Address not found exception."""

    def __init__(self, address_id: UUID | None = None, user_id: UUID | None = None) -> None:
        """Initialize AddressNotFoundError."""
        super().__init__(resource="Address", identifier=address_id)
        # Add user_id to details if provided
        if user_id:
            self.details["user_id"] = str(user_id)


class CategoryNotFoundError(NotFoundError):
    """Category not found exception."""

    def __init__(self, category_id: UUID | None = None, slug: str | None = None) -> None:
        """Initialize CategoryNotFoundError."""
        identifier = category_id if category_id else slug
        super().__init__(resource="Category", identifier=identifier)
        # Add slug to details if provided (when looking up by slug)
        if slug and not category_id:
            self.details["slug"] = slug


class WishlistItemNotFoundError(NotFoundError):
    """Wishlist item not found exception."""

    def __init__(self, product_id: UUID | None = None, user_id: UUID | None = None) -> None:
        """Initialize WishlistItemNotFoundError."""
        super().__init__(
            resource="Wishlist item",
            identifier=product_id,
            message="Product not found in wishlist.",
        )
        if user_id:
            self.details["user_id"] = str(user_id)


# ============= Business Logic Exceptions ============= #


class ValidationError(AppError):
    """Business validation error."""

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize ValidationError."""
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class DuplicateResourceError(AppError):
    """Resource already exists."""

    def __init__(self, resource: str, field: str, value: str) -> None:
        """Initialize DuplicateResourceError."""
        super().__init__(
            message=f"{resource} with {field}='{value}' already exists.",
            status_code=409,
            error_code="DUPLICATE_RESOURCE",
            details={"resource": resource, "field": field, "value": value},
        )


class ResourceLimitError(AppError):
    """Resource limit exceeded."""

    def __init__(self, resource: str, limit: int, current: int | None = None) -> None:
        """Initialize ResourceLimitError."""
        details = {"resource": resource, "limit": limit}
        if current is not None:
            details["current"] = current
        super().__init__(
            message=f"You cannot have more than {limit} {resource.lower()}.",
            status_code=400,
            error_code="RESOURCE_LIMIT_EXCEEDED",
            details=details,
        )


class InvalidTransitionError(AppError):
    """Invalid state transition."""

    def __init__(self, entity: str, from_state: str, to_state: str) -> None:
        """Initialize InvalidTransitionError."""
        super().__init__(
            message=f"Cannot transition {entity} from {from_state} to {to_state}.",
            status_code=400,
            error_code="INVALID_TRANSITION",
            details={
                "entity": entity,
                "from_state": from_state,
                "to_state": to_state,
            },
        )


class SelfReferenceError(ValidationError):
    """Entity cannot reference itself."""

    def __init__(self, entity: str, field: str = "parent") -> None:
        """Initialize SelfReferenceError."""
        super().__init__(
            message=f"{entity} cannot be its own {field}.",
            field=field,
        )


# ============= Authentication & Authorization ============= #


class AuthenticationError(AppError):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed.") -> None:
        """Initialize AuthenticationError."""
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_FAILED",
        )


class AuthorizationError(AppError):
    """Authorization failed."""

    def __init__(self, message: str = "You don't have permission to perform this action.") -> None:
        """Initialize AuthorizationError."""
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_FAILED",
        )


class InvalidCredentialsError(AuthenticationError):
    """Invalid email or password."""

    def __init__(self) -> None:
        """Initialize InvalidCredentialsError."""
        super().__init__(message="Invalid email or password.")


class PasswordMismatchError(AuthenticationError):
    """Current password is incorrect."""

    def __init__(self) -> None:
        """Initialize PasswordMismatchError."""
        super().__init__(message="Current password is incorrect.")


class SelfModificationError(AuthorizationError):
    """Cannot modify own resource."""

    def __init__(self, action: str = "this action") -> None:
        """Initialize SelfModificationError."""
        super().__init__(message=f"You cannot perform {action} on your own account.")


# ============= Business-Specific Exceptions ============= #


class InsufficientStockError(AppError):
    """Product out of stock."""

    def __init__(self, product_name: str, requested: int, available: int) -> None:
        """Initialize InsufficientStockError."""
        super().__init__(
            message=f"Insufficient stock for '{product_name}'. Requested: {requested}, Available: {available}.",
            status_code=400,
            error_code="INSUFFICIENT_STOCK",
            details={
                "product": product_name,
                "requested": requested,
                "available": available,
            },
        )


class DuplicateReviewError(AppError):
    """User already reviewed this product."""

    def __init__(self) -> None:
        """Initialize DuplicateReviewError."""
        super().__init__(
            message="You have already reviewed this product.",
            status_code=409,
            error_code="DUPLICATE_REVIEW",
        )


class ProductInactiveError(AppError):
    """Product is not available for purchase."""

    def __init__(self, product_name: str | None = None) -> None:
        """Initialize ProductInactiveError."""
        message = (
            f"Product '{product_name}' is not available."
            if product_name
            else "Product is not available."
        )
        super().__init__(
            message=message,
            status_code=400,
            error_code="PRODUCT_INACTIVE",
            details={"product": product_name} if product_name else {},
        )


class ProductNotInCartError(NotFoundError):
    """Product not found in cart."""

    def __init__(self, product_id: UUID | None = None) -> None:
        """Initialize ProductNotInCartError."""
        super().__init__(
            resource="Product in cart",
            identifier=product_id,
            message="Product not found in cart.",
        )


class InvalidCartSessionError(ValidationError):
    """Invalid cart session."""

    def __init__(self, message: str = "Session ID is required for guest cart operations.") -> None:
        """Initialize InvalidCartSessionError."""
        super().__init__(message=message)


class EmptyCartError(ValidationError):
    """Cart is empty."""

    def __init__(self) -> None:
        """Initialize EmptyCartError."""
        super().__init__(message="Cart is empty. Add items before placing an order.")


class PaymentGatewayError(AppError):
    """Payment gateway (Stripe) error."""

    def __init__(self, message: str, gateway: str = "Stripe") -> None:
        """Initialize PaymentGatewayError."""
        super().__init__(
            message=f"{gateway} error: {message}",
            status_code=502,
            error_code="PAYMENT_GATEWAY_ERROR",
            details={"gateway": gateway, "error": message},
        )


class WebhookValidationError(AppError):
    """Webhook validation failed."""

    def __init__(self, reason: str) -> None:
        """Initialize WebhookValidationError."""
        super().__init__(
            message=f"Webhook validation failed: {reason}",
            status_code=400,
            error_code="WEBHOOK_VALIDATION_ERROR",
            details={"reason": reason},
        )
