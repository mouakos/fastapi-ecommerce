"""Product API Routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.v1.dependencies import AdminRoleDep, ProductServiceDep
from app.schemas.common import PaginatedRead
from app.schemas.product_schema import ProductCreate, ProductDetailRead, ProductRead, ProductUpdate
from app.schemas.search_schema import (
    AvailabilityFilter,
    ProductAutocompleteRead,
    SortByField,
    SortOrder,
)

product_router = APIRouter(prefix="/products", tags=["Products"])


# Static utility paths first
@product_router.get(
    "/autocomplete",
    response_model=ProductAutocompleteRead,
    summary="Get product name suggestions",
    description="Retrieve autocomplete suggestions for product names based on search query. Returns up to 10 matching product names.",
)
async def get_product_autocomplete_suggestions(
    product_service: ProductServiceDep,
    query: Annotated[
        str,
        Query(
            min_length=2,
            max_length=255,
            description="Search query for product name autocomplete (case-insensitive)",
        ),
    ],
    limit: Annotated[int, Query(ge=1, le=10, description="Maximum number of suggestions")] = 10,
) -> ProductAutocompleteRead:
    """Get autocomplete suggestions for product names based on a search query."""
    return await product_service.get_autocomplete_suggestions(query, limit)


# Collection paths
@product_router.get(
    "",
    response_model=PaginatedRead[ProductRead],
    summary="List products",
    description="Retrieve paginated list of products with advanced filtering by category, price range, rating, and availability. Supports search and sorting.",
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
    "",
    response_model=ProductDetailRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
    description="Create a new product. Admin access required.",
    dependencies=[AdminRoleDep],
)
async def create_product(
    data: ProductCreate, product_service: ProductServiceDep
) -> ProductDetailRead:
    """Create a new product."""
    return await product_service.create(data)


# Category filter paths (more specific than parameterized paths)
@product_router.get(
    "/category/id/{category_id}",
    response_model=list[ProductRead],
    summary="Get products by category ID",
    description="Retrieve all products belonging to a specific category using the category's UUID.",
)
async def get_products_by_category_id(
    category_id: UUID, product_service: ProductServiceDep
) -> list[ProductRead]:
    """Retrieve products by category ID."""
    return await product_service.get_by_category_id(category_id)


@product_router.get(
    "/category/slug/{category_slug}",
    response_model=list[ProductRead],
    summary="Get products by category slug",
    description="Retrieve all products belonging to a specific category using the category's URL-friendly slug.",
)
async def get_products_by_category_slug(
    category_slug: str, product_service: ProductServiceDep
) -> list[ProductRead]:
    """Retrieve products by category slug."""
    return await product_service.get_by_category_slug(category_slug)


# Single product lookup paths (by ID or slug)
@product_router.get(
    "/id/{product_id}",
    response_model=ProductDetailRead,
    summary="Get product by ID",
    description="Retrieve detailed information about a specific product using its UUID.",
)
async def get_product(product_id: UUID, product_service: ProductServiceDep) -> ProductDetailRead:
    """Retrieve a product by its ID."""
    return await product_service.get_by_id(product_id)


@product_router.get(
    "/slug/{slug}",
    response_model=ProductDetailRead,
    summary="Get product by slug",
    description="Retrieve detailed information about a specific product using its URL-friendly slug.",
)
async def get_product_by_slug(slug: str, product_service: ProductServiceDep) -> ProductDetailRead:
    """Retrieve a product by its slug."""
    return await product_service.get_by_slug(slug)


# Parameterized admin operations (last)
@product_router.patch(
    "/{product_id}",
    response_model=ProductDetailRead,
    summary="Update product",
    description="Update an existing product's information. Admin access required.",
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
    summary="Delete product",
    description="Permanently delete a product from the catalog. Admin access required. This action cannot be undone.",
    dependencies=[AdminRoleDep],
)
async def delete_product(product_id: UUID, product_service: ProductServiceDep) -> None:
    """Delete a product by its ID."""
    await product_service.delete(product_id)
