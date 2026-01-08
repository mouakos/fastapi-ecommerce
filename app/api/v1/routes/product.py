"""Product API Routes."""

# mypy: disable-error-code=return-value
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import get_session
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.product import ProductService

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.get(
    "/",
    response_model=list[ProductRead],
    summary="List all products",
)
async def list_products(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ProductRead]:
    """List all products."""
    return await ProductService.list_all(session)


@router.post(
    "/",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
)
async def create_product(
    data: ProductCreate, session: Annotated[AsyncSession, Depends(get_session)]
) -> ProductRead:
    """Create a new product."""
    return await ProductService.create(session, data)


@router.get(
    "/id/{product_id}",
    response_model=ProductRead,
    summary="Retrieve a product by its ID",
)
async def get_product(
    product_id: UUID, session: Annotated[AsyncSession, Depends(get_session)]
) -> ProductRead:
    """Retrieve a product by its ID."""
    return await ProductService.get_by_id(session, product_id)


@router.get(
    "/slug/{slug}",
    response_model=ProductRead,
    summary="Retrieve a product by its slug",
)
async def get_product_by_slug(
    slug: str, session: Annotated[AsyncSession, Depends(get_session)]
) -> ProductRead:
    """Retrieve a product by its slug."""
    return await ProductService.get_by_slug(session, slug)


@router.put(
    "/{product_id}",
    response_model=ProductRead,
    summary="Update a product by its ID",
)
async def update_product(
    product_id: UUID, data: ProductUpdate, session: Annotated[AsyncSession, Depends(get_session)]
) -> ProductRead:
    """Update a product by its ID."""
    return await ProductService.update(session, product_id, data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product by its ID",
)
async def delete_product(
    product_id: UUID, session: Annotated[AsyncSession, Depends(get_session)]
) -> None:
    """Delete a product by its ID."""
    await ProductService.delete(session, product_id)
