"""Custom exceptions for the application.

Exception Hierarchy by HTTP Status Code:
-----------------------------------------

400 Bad Request - Validation Errors:
    ValidationError (base)
    ├── ResourceLimitError
    ├── SelfReferenceError
    ├── InsufficientStockError
    ├── ProductInactiveError
    ├── InvalidCartSessionError
    ├── EmptyCartError
    ├── WebhookValidationError
    └── InvalidOrderStatusError

401 Unauthorized - Authentication Errors:
    AuthenticationError (base)
    ├── InvalidCredentialsError
    └── PasswordMismatchError

403 Forbidden - Authorization Errors:
    AuthorizationError (base)
    └── SelfActionError

404 Not Found - Resource Not Found:
    NotFoundError (base)
    ├── UserNotFoundError
    ├── ProductNotFoundError
    ├── OrderNotFoundError
    ├── ReviewNotFoundError
    ├── AddressNotFoundError
    ├── CategoryNotFoundError
    ├── WishlistItemNotFoundError
    └── ProductNotInCartError

409 Conflict - Resource Conflicts:
    DuplicateResourceError (base)
    └── DuplicateReviewError

502 Bad Gateway - External Service Errors:
    PaymentGatewayError

Usage:
------
Raise exceptions in service layer:
    raise UserNotFoundError(user_id=user_id)
    raise ValidationError(message="Invalid input", field="email")

All exceptions include:
    - message: Human-readable error message
    - status_code: HTTP status code
    - error_code: Machine-readable error code (e.g., "RESOURCE_NOT_FOUND")
    - details: Dictionary with additional context
"""

from typing import Any
from uuid import UUID

# ============================================================================
# BASE EXCEPTION
# ============================================================================


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


# ============================================================================
# 400 BAD REQUEST - VALIDATION ERRORS
# ============================================================================


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


class ResourceLimitError(ValidationError):
    """Resource limit exceeded."""

    def __init__(self, resource: str, limit: int, current: int | None = None) -> None:
        """Initialize ResourceLimitError."""
        message = f"You cannot have more than {limit} {resource.lower()}."
        super().__init__(message=message)
        self.error_code = "RESOURCE_LIMIT_EXCEEDED"
        self.details = {"resource": resource, "limit": limit}
        if current is not None:
            self.details["current"] = current


class SelfReferenceError(ValidationError):
    """Entity cannot reference itself."""

    def __init__(self, entity: str, field: str = "parent") -> None:
        """Initialize SelfReferenceError."""
        super().__init__(
            message=f"{entity} cannot be its own {field}.",
            field=field,
        )


class InsufficientStockError(ValidationError):
    """Product out of stock."""

    def __init__(self, product_name: str, requested: int, available: int) -> None:
        """Initialize InsufficientStockError."""
        message = f"Insufficient stock for '{product_name}'. Requested: {requested}, Available: {available}."
        super().__init__(message=message)
        self.error_code = "INSUFFICIENT_STOCK"
        self.details = {
            "product": product_name,
            "requested": requested,
            "available": available,
        }


class ProductInactiveError(ValidationError):
    """Product is not available for purchase."""

    def __init__(self, product_name: str | None = None) -> None:
        """Initialize ProductInactiveError."""
        message = (
            f"Product '{product_name}' is not available."
            if product_name
            else "Product is not available."
        )
        super().__init__(message=message)
        self.error_code = "PRODUCT_INACTIVE"
        if product_name:
            self.details["product"] = product_name


class InvalidCartSessionError(ValidationError):  # TODO
    """Invalid cart session."""

    def __init__(self, message: str = "Session ID is required for guest cart operations.") -> None:
        """Initialize InvalidCartSessionError."""
        super().__init__(message=message)


class EmptyCartError(ValidationError):
    """Cart is empty."""

    def __init__(self) -> None:
        """Initialize EmptyCartError."""
        super().__init__(message="Cart is empty.")


class WebhookValidationError(ValidationError):  # TODO
    """Webhook validation failed."""

    def __init__(self, reason: str) -> None:
        """Initialize WebhookValidationError."""
        message = f"Webhook validation failed: {reason}"
        super().__init__(message=message)
        self.error_code = "WEBHOOK_VALIDATION_ERROR"
        self.details["reason"] = reason


class InvalidOrderStatusError(ValidationError):
    """Order status is invalid for the requested operation."""

    def __init__(self, message: str, current_status: str) -> None:
        """Initialize InvalidOrderStatusError."""
        super().__init__(message=message)
        self.error_code = "INVALID_ORDER_STATUS"
        self.details["current_status"] = current_status


# ============================================================================
# 401 UNAUTHORIZED - AUTHENTICATION ERRORS
# ============================================================================


class AuthenticationError(AppError):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed.") -> None:
        """Initialize AuthenticationError."""
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_FAILED",
        )


class InvalidCredentialsError(AuthenticationError):
    """Invalid email or password."""

    def __init__(self) -> None:
        """Initialize InvalidCredentialsError."""
        super().__init__(message="Invalid email or password.")


class IncorrectPasswordError(AuthenticationError):
    """Incorrect password provided."""

    def __init__(self) -> None:
        """Initialize IncorrectPasswordError."""
        super().__init__(message="Incorrect password provided.")


class PasswordMismatchError(AuthenticationError):
    """Current password is incorrect."""

    def __init__(self) -> None:
        """Initialize PasswordMismatchError."""
        super().__init__(message="Password mismatch.")


# ============================================================================
# 403 FORBIDDEN - AUTHORIZATION ERRORS
# ============================================================================


class AuthorizationError(AppError):
    """Authorization failed."""

    def __init__(self, message: str = "You don't have permission to perform this action.") -> None:
        """Initialize AuthorizationError."""
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_FAILED",
        )


class SelfActionError(AuthorizationError):
    """Cannot perform action on own account."""

    def __init__(self, action: str = "this action") -> None:
        """Initialize SelfActionError."""
        super().__init__(message=f"You cannot perform {action} on your own account.")


# ============================================================================
# 404 NOT FOUND - RESOURCE NOT FOUND ERRORS
# ============================================================================


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


class OrderNotFoundError(NotFoundError):
    """Order not found exception."""

    def __init__(self, order_id: UUID | None = None, user_id: UUID | None = None) -> None:
        """Initialize OrderNotFoundError."""
        message = "Order not found for the specified user." if user_id else None
        super().__init__(resource="Order", identifier=order_id, message=message)
        if user_id:
            self.details["user_id"] = str(user_id)


class ReviewNotFoundError(NotFoundError):
    """Review not found exception."""

    def __init__(self, *, review_id: UUID | None = None, user_id: UUID | None = None) -> None:
        """Initialize ReviewNotFoundError."""
        message = "Review not found for the specified user." if user_id else None
        super().__init__(resource="Review", identifier=review_id, message=message)
        if user_id:
            self.details["user_id"] = str(user_id)


class AddressNotFoundError(NotFoundError):
    """Address not found exception."""

    def __init__(self, address_id: UUID | None = None, user_id: UUID | None = None) -> None:
        """Initialize AddressNotFoundError."""
        message = "Address not found for the specified user." if user_id else None
        super().__init__(resource="Address", identifier=address_id, message=message)
        if user_id:
            self.details["user_id"] = str(user_id)


class CategoryNotFoundError(NotFoundError):
    """Category not found exception."""

    def __init__(self, category_id: UUID | None = None, slug: str | None = None) -> None:
        """Initialize CategoryNotFoundError."""
        identifier = category_id if category_id else slug
        super().__init__(resource="Category", identifier=identifier)


class WishlistItemNotFoundError(NotFoundError):  # TODO
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


class ProductNotInCartError(NotFoundError):  # TODO
    """Product not found in cart."""

    def __init__(self, product_id: UUID | None = None) -> None:
        """Initialize ProductNotInCartError."""
        super().__init__(
            resource="Product in cart",
            identifier=product_id,
            message="Product not found in cart.",
        )


# ============================================================================
# 409 CONFLICT - RESOURCE CONFLICT ERRORS
# ============================================================================


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


class DuplicateReviewError(DuplicateResourceError):
    """User already reviewed this product."""

    def __init__(self, product_id: UUID | None = None, user_id: UUID | None = None) -> None:
        """Initialize DuplicateReviewError."""
        super().__init__(
            resource="Review",
            field="product",
            value=str(product_id) if product_id else "this product",
        )
        self.message = "You have already reviewed this product."
        self.error_code = "DUPLICATE_REVIEW"
        if user_id:
            self.details["user_id"] = str(user_id)


# ============================================================================
# 502 BAD GATEWAY - EXTERNAL SERVICE ERRORS
# ============================================================================


class PaymentGatewayError(AppError):  # TODO
    """Payment gateway (Stripe) error."""

    def __init__(self, message: str, gateway: str = "Stripe") -> None:
        """Initialize PaymentGatewayError."""
        super().__init__(
            message=f"{gateway} error: {message}",
            status_code=502,
            error_code="PAYMENT_GATEWAY_ERROR",
            details={"gateway": gateway, "error": message},
        )
