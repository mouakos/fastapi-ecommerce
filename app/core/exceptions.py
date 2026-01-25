"""Application-specific exceptions.

This module defines custom exception classes for handling various error scenarios
within the application. Each exception class provides meaningful error messages and
status codes to facilitate error handling and debugging.
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
        error_code: str = "internal_error",
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

    def __init__(
        self, message: str = "Invalid request", error_code: str = "invalid_request"
    ) -> None:
        """Initialize ValidationError."""
        super().__init__(
            message=message,
            status_code=400,
            error_code=error_code,
        )


class ResourceLimitError(ValidationError):
    """Resource limit exceeded."""

    def __init__(self, resource: str, limit: int, current: int) -> None:
        """Initialize ResourceLimitError."""
        message = f"You cannot have more than {limit} {resource.lower()}."
        super().__init__(message=message, error_code="resource_limit_exceeded")
        self.details = {"resource": resource, "limit": limit, "current": current}


class CategorySelfReferenceError(ValidationError):
    """Category cannot be its own parent."""

    def __init__(self, category_id: UUID) -> None:
        """Initialize CategorySelfReferenceError."""
        super().__init__(
            message="Category cannot be its own parent.",
            error_code="category_self_reference",
        )
        self.details["category_id"] = str(category_id)


class InsufficientStockError(ValidationError):
    """Product out of stock."""

    def __init__(self, product_id: UUID, requested: int, available: int) -> None:
        """Initialize InsufficientStockError."""
        message = "Product has insufficient stock."
        super().__init__(message=message, error_code="insufficient_stock")
        self.details["product_id"] = str(product_id)
        self.details["requested"] = requested
        self.details["available"] = available


class ProductInactiveError(ValidationError):
    """Product is not available for purchase."""

    def __init__(self, product_id: UUID) -> None:
        """Initialize ProductInactiveError."""
        message = "Product is not available for purchase."
        super().__init__(message=message, error_code="product_inactive")
        self.details["product_id"] = str(product_id)


class InvalidCartSessionError(ValidationError):
    """Invalid cart session."""

    def __init__(self, message: str = "Session ID is required for guest cart operations.") -> None:
        """Initialize InvalidCartSessionError."""
        super().__init__(message=message, error_code="invalid_cart_session")


class EmptyCartError(ValidationError):
    """Cart is empty."""

    def __init__(self, cart_id: UUID) -> None:
        """Initialize EmptyCartError."""
        super().__init__(message="Cart is empty.", error_code="empty_cart")
        self.details["cart_id"] = str(cart_id)


class WebhookValidationError(ValidationError):
    """Webhook validation failed."""

    def __init__(self, reason: str) -> None:
        """Initialize WebhookValidationError."""
        message = f"Webhook validation failed: {reason}"
        super().__init__(message=message, error_code="webhook_validation_error")
        self.details["reason"] = reason


class InvalidOrderStatusError(ValidationError):
    """Order status is invalid for the requested operation."""

    def __init__(self, order_id: UUID, current_status: str, expected_status: str) -> None:
        """Initialize InvalidOrderStatusError."""
        super().__init__(
            message="Invalid order status for the requested operation.",
            error_code="invalid_order_status",
        )
        self.details["order_id"] = str(order_id)
        self.details["current_status"] = current_status
        self.details["expected_status"] = expected_status


class PasswordMismatchError(ValidationError):
    """Password and confirmation do not match."""

    def __init__(self) -> None:
        """Initialize PasswordMismatchError."""
        super().__init__(
            message="Password and confirmation do not match.", error_code="password_mismatch"
        )


class InactiveUserError(ValidationError):
    """User account is inactive."""

    def __init__(self, user_id: UUID) -> None:
        """Initialize InactiveUserError."""
        super().__init__(message="User account is inactive.", error_code="inactive_user")
        self.details["user_id"] = str(user_id)


# ============================================================================
# 401 UNAUTHORIZED - AUTHENTICATION ERRORS
# ============================================================================


class AuthenticationError(AppError):
    """Authentication failed."""

    def __init__(
        self,
        message: str = "Authentication failed.",
        error_code: str = "authentication_failed",
    ) -> None:
        """Initialize AuthenticationError."""
        super().__init__(
            message=message,
            status_code=401,
            error_code=error_code,
        )


class InvalidCredentialsError(AuthenticationError):
    """Invalid email or password."""

    def __init__(self) -> None:
        """Initialize InvalidCredentialsError."""
        super().__init__(message="Invalid email or password.", error_code="invalid_credentials")


class IncorrectPasswordError(AuthenticationError):
    """Incorrect password provided."""

    def __init__(self) -> None:
        """Initialize IncorrectPasswordError."""
        super().__init__(message="Incorrect password provided.", error_code="incorrect_password")


# ============================================================================
# 403 FORBIDDEN - AUTHORIZATION ERRORS
# ============================================================================


class AuthorizationError(AppError):
    """Authorization failed."""

    def __init__(
        self,
        message: str = "You don't have permission to perform this action.",
        error_code: str = "authorization_failed",
    ) -> None:
        """Initialize AuthorizationError."""
        super().__init__(
            message=message,
            status_code=403,
            error_code=error_code,
        )


class SelfActionError(AuthorizationError):
    """Cannot perform action on own account."""

    def __init__(self, user_id: UUID, action: str = "perform this action") -> None:
        """Initialize SelfActionError."""
        super().__init__(
            message=f"You cannot {action}.",
            error_code="self_action_forbidden",
        )
        self.details["user_id"] = str(user_id)


# ============================================================================
# 404 NOT FOUND - RESOURCE NOT FOUND ERRORS
# ============================================================================


class NotFoundError(AppError):
    """Base exception for not found errors."""

    def __init__(
        self,
        resource: str,
        message: str | None = None,
        error_code: str = "resource_not_found",
    ) -> None:
        """Initialize NotFoundError."""
        msg = message or f"{resource} not found."
        super().__init__(
            message=msg,
            status_code=404,
            error_code=error_code,
        )
        self.details["resource"] = resource


class UserNotFoundError(NotFoundError):
    """User not found exception."""

    def __init__(self, user_id: UUID) -> None:
        """Initialize UserNotFoundError."""
        super().__init__(resource="User", error_code="user_not_found")
        self.details["user_id"] = str(user_id)


class ProductNotFoundError(NotFoundError):
    """Product not found exception."""

    def __init__(self, *, product_id: UUID | None = None, slug: str | None = None) -> None:
        """Initialize ProductNotFoundError."""
        super().__init__(resource="Product", error_code="product_not_found")
        if product_id is not None:
            self.details["product_id"] = str(product_id)
        if slug is not None:
            self.details["slug"] = slug


class OrderNotFoundError(NotFoundError):
    """Order not found exception."""

    def __init__(self, *, order_id: UUID, user_id: UUID | None = None) -> None:
        """Initialize OrderNotFoundError."""
        super().__init__(resource="Order", error_code="order_not_found")
        self.details["order_id"] = str(order_id)
        if user_id is not None:
            self.details["user_id"] = str(user_id)


class ReviewNotFoundError(NotFoundError):
    """Review not found exception."""

    def __init__(self, *, review_id: UUID, user_id: UUID | None = None) -> None:
        """Initialize ReviewNotFoundError."""
        super().__init__(resource="Review", error_code="review_not_found")
        self.details["review_id"] = str(review_id)
        if user_id is not None:
            self.details["user_id"] = str(user_id)


class AddressNotFoundError(NotFoundError):
    """Address not found exception."""

    def __init__(self, *, address_id: UUID, user_id: UUID) -> None:
        """Initialize AddressNotFoundError."""
        super().__init__(resource="Address", error_code="address_not_found")
        self.details["address_id"] = str(address_id)
        self.details["user_id"] = str(user_id)


class CategoryNotFoundError(NotFoundError):
    """Category not found exception."""

    def __init__(self, *, category_id: UUID | None = None, slug: str | None = None) -> None:
        """Initialize CategoryNotFoundError."""
        super().__init__(resource="Category", error_code="category_not_found")
        if category_id is not None:
            self.details["category_id"] = str(category_id)
        if slug is not None:
            self.details["slug"] = slug


class ProductNotInWishlistError(NotFoundError):
    """Product is not in the user's wishlist."""

    def __init__(self, *, product_id: UUID, user_id: UUID) -> None:
        """Initialize ProductNotInWishlistError."""
        super().__init__(
            resource="Wishlist item",
            message="Product not found in wishlist.",
            error_code="product_not_in_wishlist",
        )
        self.details["product_id"] = str(product_id)
        self.details["user_id"] = str(user_id)


class ProductNotInCartError(NotFoundError):
    """Product is not in the user's cart."""

    def __init__(self, *, product_id: UUID, cart_id: UUID) -> None:
        """Initialize ProductNotInCartError."""
        super().__init__(
            resource="Cart item",
            message="Product not found in cart.",
            error_code="product_not_in_cart",
        )
        self.details["product_id"] = str(product_id)
        self.details["cart_id"] = str(cart_id)


# ============================================================================
# 409 CONFLICT - RESOURCE CONFLICT ERRORS
# ============================================================================


class DuplicateResourceError(AppError):
    """Resource already exists."""

    def __init__(
        self,
        *,
        resource: str,
        message: str = "Resource already exists.",
        error_code: str = "duplicate_resource",
    ) -> None:
        """Initialize DuplicateResourceError."""
        super().__init__(
            message=message,
            status_code=409,
            error_code=error_code,
            details={"resource": resource},
        )


class DuplicateUserError(DuplicateResourceError):
    """User with this email already exists."""

    def __init__(self, *, email: str) -> None:
        """Initialize DuplicateUserError."""
        super().__init__(
            resource="User",
            message="User with this email already exists.",
            error_code="duplicate_user",
        )
        self.details["email"] = email


class DuplicateReviewError(DuplicateResourceError):
    """User already reviewed this product."""

    def __init__(self, *, product_id: UUID, user_id: UUID) -> None:
        """Initialize DuplicateReviewError."""
        super().__init__(
            resource="Review",
            message="Product already reviewed by user.",
            error_code="duplicate_review",
        )
        self.details["product_id"] = str(product_id)
        self.details["user_id"] = str(user_id)


class DuplicateWishlistItemError(DuplicateResourceError):
    """Product already in user's wishlist."""

    def __init__(self, *, product_id: UUID, user_id: UUID) -> None:
        """Initialize DuplicateWishlistItemError."""
        super().__init__(
            resource="Wishlist item",
            message="Product already in wishlist.",
            error_code="duplicate_wishlist_item",
        )
        self.details["product_id"] = str(product_id)
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
            error_code="payment_gateway_error",
            details={"gateway": gateway, "error": message},
        )
