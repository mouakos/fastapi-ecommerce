"""Product API Routes."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.v1.dependencies import AdminRoleDep, ProductServiceDep
from app.schemas.product_schema import ProductCreate, ProductRead, ProductUpdate

product_router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@product_router.get(
    "/",
    response_model=list[ProductRead],
    summary="List all products",
)
async def list_products(
    product_service: ProductServiceDep,
) -> list[ProductRead]:
    """List all products."""
    return await product_service.list_all()


@product_router.post(
    "/",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    dependencies=[AdminRoleDep],
)
async def create_product(data: ProductCreate, product_service: ProductServiceDep) -> ProductRead:
    """Create a new product."""
    return await product_service.create(data)


@product_router.get(
    "/id/{product_id}",
    response_model=ProductRead,
    summary="Retrieve a product by its ID",
)
async def get_product(product_id: UUID, product_service: ProductServiceDep) -> ProductRead:
    """Retrieve a product by its ID."""
    return await product_service.get_by_id(product_id)


@product_router.get(
    "/slug/{slug}",
    response_model=ProductRead,
    summary="Retrieve a product by its slug",
)
async def get_product_by_slug(slug: str, product_service: ProductServiceDep) -> ProductRead:
    """Retrieve a product by its slug."""
    return await product_service.get_by_slug(slug)


@product_router.put(
    "/{product_id}",
    response_model=ProductRead,
    summary="Update a product by its ID",
    dependencies=[AdminRoleDep],
)
async def update_product(
    product_id: UUID, data: ProductUpdate, product_service: ProductServiceDep
) -> ProductRead:
    """Update a product by its ID."""
    return await product_service.update(product_id, data)


@product_router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product by its ID",
    dependencies=[AdminRoleDep],
)
async def delete_product(product_id: UUID, product_service: ProductServiceDep) -> None:
    """Delete a product by its ID."""
    await product_service.delete(product_id)
