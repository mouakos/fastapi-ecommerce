"""Product API Routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.v1.dependencies import AdminRoleDep, ProductServiceDep
from app.schemas.common import PaginatedRead
from app.schemas.product_schema import ProductCreate, ProductDetailRead, ProductRead, ProductUpdate
from app.schemas.search_schema import (
    AvailabilityFilter,
    SortByField,
    SortOrder,
)

product_router = APIRouter(prefix="/products", tags=["Products"])


@product_router.get(
    "/",
    response_model=PaginatedRead[ProductRead],
    summary="List all products with optional filters, sorting, and pagination",
)
async def list_products(
    product_service: ProductServiceDep,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    per_page: Annotated[int, Query(ge=1, le=100, description="Number of items per page")] = 10,
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=255,
            description="Search query for product name or description (case-insensitive)",
        ),
    ] = None,
    category_id: Annotated[UUID | None, Query(description="Filter by category ID")] = None,
    min_price: Annotated[float | None, Query(ge=0, description="Minimum price")] = None,
    max_price: Annotated[float | None, Query(ge=0, description="Maximum price")] = None,
    min_rating: Annotated[
        int | None, Query(ge=1, le=5, description="Minimum average rating (1-5)")
    ] = None,
    availability: Annotated[
        AvailabilityFilter, Query(description="Stock availability")
    ] = AvailabilityFilter.ALL,
    sort_by: Annotated[SortByField, Query(description="Sort by field")] = SortByField.ID,
    sort_order: Annotated[SortOrder, Query(description="Sort order")] = SortOrder.ASC,
) -> PaginatedRead[ProductRead]:
    """List all products with optional filters, sorting, and pagination."""
    return await product_service.list_all(
        page=page,
        per_page=per_page,
        search=search,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        availability=availability,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@product_router.post(
    "/",
    response_model=ProductDetailRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    dependencies=[AdminRoleDep],
)
async def create_product(
    data: ProductCreate, product_service: ProductServiceDep
) -> ProductDetailRead:
    """Create a new product."""
    return await product_service.create(data)


@product_router.get(
    "/id/{product_id}",
    response_model=ProductDetailRead,
    summary="Retrieve a product by its ID",
)
async def get_product(product_id: UUID, product_service: ProductServiceDep) -> ProductDetailRead:
    """Retrieve a product by its ID."""
    return await product_service.get_by_id(product_id)


@product_router.get(
    "/slug/{slug}",
    response_model=ProductDetailRead,
    summary="Retrieve a product by its slug",
)
async def get_product_by_slug(slug: str, product_service: ProductServiceDep) -> ProductDetailRead:
    """Retrieve a product by its slug."""
    return await product_service.get_by_slug(slug)


@product_router.put(
    "/{product_id}",
    response_model=ProductDetailRead,
    summary="Update a product by its ID",
    dependencies=[AdminRoleDep],
)
async def update_product(
    product_id: UUID, data: ProductUpdate, product_service: ProductServiceDep
) -> ProductDetailRead:
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
