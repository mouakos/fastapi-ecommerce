"""API Routes dependencies."""

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, Response, status
from fastapi.params import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import decode_access_token
from app.db.database import AsyncSessionLocal
from app.interfaces.unit_of_work import UnitOfWork
from app.schemas.user_schema import UserRead
from app.services.address_service import AddressService
from app.services.cart_service import CartService
from app.services.category_service import CategoryService
from app.services.product_service import ProductService
from app.services.user_service import UserService
from app.uow.sql_unit_of_work import SqlUnitOfWork

oauth_scheme = HTTPBearer(
    scheme_name="Bearer",
    auto_error=False,
    description="JWT Access Token in the Authorization header",
)

TokenDep = Annotated[HTTPAuthorizationCredentials, Depends(oauth_scheme)]


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for the duration of a request."""
    async with AsyncSessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_uow(session: SessionDep) -> AsyncGenerator[UnitOfWork, None]:
    """Get Unit of Work."""
    async with SqlUnitOfWork(session) as uow:
        yield uow


UnitOfWorkDep = Annotated[UnitOfWork, Depends(get_uow)]


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


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AddressServiceDep = Annotated[AddressService, Depends(get_address_service)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]
CartServiceDep = Annotated[CartService, Depends(get_cart_service)]


async def get_current_user(
    credentials: TokenDep,
    user_service: UserServiceDep,
) -> UserRead:
    """Get current authenticated user from JWT token."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    decoded_token = decode_access_token(token=credentials.credentials)
    if not decoded_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decoded_token.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return await user_service.get_by_id(UUID(user_id))
    except HTTPException as exc:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None
        raise


CurrentUserDep = Annotated[UserRead, Depends(get_current_user)]


async def get_optional_current_user(
    credentials: TokenDep,
    user_service: UserServiceDep,
) -> UserRead | None:
    """Get current authenticated user from JWT token, or None if not authenticated."""
    try:
        return await get_current_user(credentials, user_service)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        raise


OptionalCurrentUserDep = Annotated[UserRead | None, Depends(get_optional_current_user)]

# Cart session constants
CART_SESSION_COOKIE = "cart_session_id"
CART_SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


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
