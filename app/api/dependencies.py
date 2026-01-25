"""API Routes dependencies."""

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.constants import CART_SESSION_COOKIE, CART_SESSION_MAX_AGE, REFRESH_TOKEN_COOKIE
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InactiveUserError,
    UserNotFoundError,
)
from app.core.security import decode_token, is_token_revoked
from app.db.database import get_session
from app.interfaces.unit_of_work import UnitOfWork
from app.models.user import User, UserRole
from app.schemas.auth import TokenData, TokenType
from app.services.address_service import AddressService
from app.services.admin_service import AdminService
from app.services.cart_service import CartService
from app.services.category_service import CategoryService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.services.product_service import ProductService
from app.services.review_service import ReviewService
from app.services.user_service import UserService
from app.services.wishlist_service import WishlistService
from app.uow.sql_unit_of_work import SqlUnitOfWork

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]
RequestFormDep = Annotated[OAuth2PasswordRequestForm, Depends()]


async def get_uow(session: SessionDep) -> AsyncGenerator[UnitOfWork, None]:
    """Get Unit of Work."""
    async with SqlUnitOfWork(session) as uow:
        yield uow


UnitOfWorkDep = Annotated[UnitOfWork, Depends(get_uow)]


def get_payment_service(uow: UnitOfWorkDep) -> PaymentService:
    """Get Payment Service."""
    return PaymentService(uow)


def get_user_service(uow: UnitOfWorkDep) -> UserService:
    """Get User Service."""
    return UserService(uow)


def get_product_service(uow: UnitOfWorkDep) -> ProductService:
    """Get Product Service."""
    return ProductService(uow)


def get_category_service(uow: UnitOfWorkDep) -> CategoryService:
    """Get Category Service."""
    return CategoryService(uow)


def get_address_service(uow: UnitOfWorkDep) -> AddressService:
    """Get Address Service."""
    return AddressService(uow)


def get_cart_service(uow: UnitOfWorkDep) -> CartService:
    """Get Cart Service."""
    return CartService(uow)


def get_order_service(uow: UnitOfWorkDep) -> OrderService:
    """Get Order Service."""
    return OrderService(uow)


def get_wishlist_service(uow: UnitOfWorkDep) -> WishlistService:
    """Get Wishlist Service."""
    return WishlistService(uow)


def get_review_service(uow: UnitOfWorkDep) -> ReviewService:
    """Get Review Service."""
    return ReviewService(uow)


def get_admin_service(uow: UnitOfWorkDep) -> AdminService:
    """Get Admin Service."""
    return AdminService(uow)


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AddressServiceDep = Annotated[AddressService, Depends(get_address_service)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]
CartServiceDep = Annotated[CartService, Depends(get_cart_service)]
WishlistServiceDep = Annotated[WishlistService, Depends(get_wishlist_service)]
PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]
AdminServiceDep = Annotated[AdminService, Depends(get_admin_service)]


async def get_access_token_data(
    token: TokenDep,
) -> TokenData:
    """Get access token data from JWT token."""
    token_data = decode_token(token)
    if not token_data:
        raise AuthenticationError(message="Could not validate credentials.")

    if token_data.type != TokenType.ACCESS:
        raise AuthenticationError(message="Invalid access token.")

    if await is_token_revoked(token_data.jti):
        raise AuthenticationError(message="Token has been revoked.")

    return token_data


async def get_refresh_token_data(
    request: Request,
) -> TokenData:
    """Get refresh token data from JWT token in cookies."""
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if not refresh_token:
        raise AuthenticationError(message="Refresh token not found.")

    token_data = decode_token(refresh_token)
    if not token_data:
        raise AuthenticationError(message="Could not validate credentials.")

    if token_data.type != TokenType.REFRESH:
        raise AuthenticationError(message="Invalid refresh token.")

    if await is_token_revoked(token_data.jti):
        raise AuthenticationError(message="Token has been revoked.")

    return token_data


RefreshTokenDataDep = Annotated[TokenData, Depends(get_refresh_token_data)]
AccessTokenDataDep = Annotated[TokenData, Depends(get_access_token_data)]


async def get_current_user(
    token_data: AccessTokenDataDep,
    user_service: UserServiceDep,
) -> User:
    """Get current authenticated user from JWT token."""
    if await is_token_revoked(token_data.jti):
        raise AuthenticationError(message="Token has been revoked.")

    try:
        user = await user_service.get_user(token_data.user_id)
    except UserNotFoundError as exc:
        raise AuthenticationError(message="Could not validate credentials.") from exc
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise InactiveUserError(user_id=current_user.id)
    return current_user


async def get_optional_current_user(
    token_data: AccessTokenDataDep,
    user_service: UserServiceDep,
) -> User | None:
    """Get current authenticated user from JWT token, or None if not authenticated."""
    try:
        user = await get_current_user(token_data, user_service)
        return user if user.is_active else None
    except AuthenticationError:
        return None


CurrentUserDep = Annotated[User, Depends(get_current_active_user)]
OptionalCurrentUserDep = Annotated[User | None, Depends(get_optional_current_user)]


class RoleChecker:
    """Dependency to check if the current user has one of the allowed roles."""

    def __init__(self, allowed_roles: list[UserRole]) -> None:
        """Initialize the RoleChecker with allowed roles."""
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: CurrentUserDep) -> bool:
        """Check if the current user has one of the allowed roles."""
        if current_user.role in self.allowed_roles:
            return True

        raise AuthorizationError()


AdminRoleDep = Depends(RoleChecker([UserRole.ADMIN]))


def get_cart_session_id(request: Request) -> str | None:
    """Get cart session ID from cookies.

    Args:
        request (Request): FastAPI request object.

    Returns:
        str | None: Session ID or None if not found.
    """
    return request.cookies.get(CART_SESSION_COOKIE)


def get_or_create_cart_session_id(request: Request, response: Response) -> str:
    """Get or create a cart session ID.

    Args:
        request (Request): FastAPI request object.
        response (Response): FastAPI response object.

    Returns:
        str: Session ID.
    """
    session_id = request.cookies.get(CART_SESSION_COOKIE)
    if not session_id:
        session_id = str(uuid4())
        response.set_cookie(
            key=CART_SESSION_COOKIE,
            value=session_id,
            httponly=True,
            samesite="lax",
            max_age=CART_SESSION_MAX_AGE,
        )
    return session_id


CartSessionIdDep = Annotated[str | None, Depends(get_cart_session_id)]
CartSessionIdOrCreateDep = Annotated[str, Depends(get_or_create_cart_session_id)]
