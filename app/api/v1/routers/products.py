"""Product catalog API routes with advanced filtering, search, and CRUD operations."""
# mypy: disable-error-code=return-value

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.v1.dependencies import AdminRoleDep, ProductServiceDep
from app.schemas.common import Page
from app.schemas.product import ProductCreate, ProductDetailRead, ProductRead, ProductUpdate
from app.schemas.search import (
    AvailabilityFilter,
    ProductAutocompleteRead,
    SortByField,
    SortOrder,
)
from app.utils.pagination import build_page

router = APIRouter(prefix="/products", tags=["Products"])


# Static utility paths first
@router.get(
    "/autocomplete",
    response_model=ProductAutocompleteRead,
    summary="Get product name suggestions",
    description="Retrieve autocomplete suggestions for product names based on search query. Returns up to 10 matching product names.",
)
async def autocomplete(
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
    """List autocomplete suggestions for product names based on a search query."""
    suggestions = await product_service.list_autocomplete_suggestions(query, limit)
    return ProductAutocompleteRead(suggestions=suggestions)


# Collection paths
@router.get(
    "",
    response_model=Page[ProductRead],
    summary="List products",
    description="Retrieve paginated list of products with advanced filtering by category, price range, rating, and availability. Supports search and sorting.",
)
async def list_all(
    product_service: ProductServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Number of items per page"),
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=255,
            description="Search query for product name or description (case-insensitive)",
        ),
    ] = None,
    category_id: Annotated[UUID | None, Query(description="Filter by category ID")] = None,
    category_slug: Annotated[str | None, Query(description="Filter by category slug")] = None,
    min_price: Annotated[float | None, Query(ge=0, description="Minimum price")] = None,
    max_price: Annotated[float | None, Query(ge=0, description="Maximum price")] = None,
    min_rating: Annotated[
        int | None, Query(ge=1, le=5, description="Minimum average rating (1-5)")
    ] = None,
    availability: Annotated[
        AvailabilityFilter, Query(description="Stock availability")
    ] = AvailabilityFilter.ALL,
    sort_by: Annotated[SortByField, Query(description="Sort by field")] = SortByField.CREATED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort order")] = SortOrder.ASC,
) -> Page[ProductRead]:
    """List all products with optional filters, sorting, and pagination."""
    products, total = await product_service.list_all(
        page=page,
        per_page=per_page,
        search=search,
        category_id=category_id,
        category_slug=category_slug,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        availability=availability.value,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
    )
    return build_page(items=products, total=total, page=page, size=per_page)  # type: ignore [arg-type]


@router.post(
    "",
    response_model=ProductDetailRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
    description="Create a new product. Admin access required.",
    dependencies=[AdminRoleDep],
)
async def create(data: ProductCreate, product_service: ProductServiceDep) -> ProductDetailRead:
    """Create a new product."""
    product = await product_service.create(data)
    return ProductDetailRead(
        **product.model_dump(),
        review_count=await product_service.count_reviews(product.id),
        average_rating=await product_service.calculate_average_rating(product.id),
    )


# Single product lookup paths (by ID or slug)
@router.get(
    "/id/{product_id}",
    response_model=ProductDetailRead,
    summary="Get product by ID",
    description="Retrieve detailed information about a specific product using its UUID.",
)
async def get(product_id: UUID, product_service: ProductServiceDep) -> ProductDetailRead:
    """Retrieve a product by its ID."""
    product = await product_service.find_by_id(product_id)
    return ProductDetailRead(
        **product.model_dump(),
        review_count=await product_service.count_reviews(product_id),
        average_rating=await product_service.calculate_average_rating(product_id),
    )


@router.get(
    "/slug/{slug}",
    response_model=ProductDetailRead,
    summary="Get product by slug",
    description="Retrieve detailed information about a specific product using its URL-friendly slug.",
)
async def get_by_slug(slug: str, product_service: ProductServiceDep) -> ProductDetailRead:
    """Retrieve a product by its slug."""
    product = await product_service.find_by_slug(slug)
    return ProductDetailRead(
        **product.model_dump(),
        review_count=await product_service.count_reviews(product.id),
        average_rating=await product_service.calculate_average_rating(product.id),
    )


# Parameterized admin operations (last)
@router.patch(
    "/{product_id}",
    response_model=ProductDetailRead,
    summary="Update product",
    description="Update an existing product's information. Admin access required.",
    dependencies=[AdminRoleDep],
)
async def update(
    product_id: UUID, data: ProductUpdate, product_service: ProductServiceDep
) -> ProductDetailRead:
    """Update a product by its ID."""
    product = await product_service.update(product_id, data)
    return ProductDetailRead(
        **product.model_dump(),
        review_count=await product_service.count_reviews(product_id),
        average_rating=await product_service.calculate_average_rating(product_id),
    )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
    description="Permanently delete a product from the catalog. Admin access required. This action cannot be undone.",
    dependencies=[AdminRoleDep],
)
async def delete(product_id: UUID, product_service: ProductServiceDep) -> None:
    """Delete a product by its ID."""
    await product_service.delete(product_id)
