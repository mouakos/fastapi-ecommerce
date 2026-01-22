"""Product catalog API routes with advanced filtering, search, and CRUD operations."""
# mypy: disable-error-code=return-value

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.v1.dependencies import AdminRoleDep, ProductServiceDep
from app.schemas.common import Page, SortOrder
from app.schemas.product import (
    ProductAutocompleteResponse,
    ProductAvailabilityFilter,
    ProductCreate,
    ProductDetail,
    ProductPublic,
    ProductSortByField,
    ProductUpdate,
)
from app.utils.pagination import build_page

router = APIRouter()


@router.get(
    "/autocomplete",
    response_model=ProductAutocompleteResponse,
    summary="Get product name suggestions",
    description="Retrieve autocomplete suggestions for product names based on search query. Returns up to 10 matching product names.",
)
async def get_autocomplete_suggestions(
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
) -> ProductAutocompleteResponse:
    """List autocomplete suggestions for product names based on a search query."""
    suggestions = await product_service.get_autocomplete_suggestions(query, limit)
    return ProductAutocompleteResponse(suggestions=suggestions)


@router.get(
    "",
    response_model=Page[ProductPublic],
    summary="Get all products",
    description="Retrieve paginated list of products with advanced filtering by category, price range, rating, and availability. Supports search and sorting.",
)
async def get_products(
    product_service: ProductServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
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
    min_price: Annotated[Decimal | None, Query(ge=0, description="Minimum price")] = None,
    max_price: Annotated[Decimal | None, Query(ge=0, description="Maximum price")] = None,
    min_rating: Annotated[
        int | None, Query(ge=1, le=5, description="Minimum average rating (1-5)")
    ] = None,
    availability: Annotated[
        ProductAvailabilityFilter, Query(description="Stock availability")
    ] = ProductAvailabilityFilter.ALL,
    sort_by: Annotated[
        ProductSortByField, Query(description="Sort by field")
    ] = ProductSortByField.CREATED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort order")] = SortOrder.ASC,
) -> Page[ProductPublic]:
    """Get all products with optional filters, sorting, and pagination."""
    products, total = await product_service.get_products(
        page=page,
        page_size=page_size,
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
    return build_page(items=products, total=total, page=page, size=page_size)  # type: ignore [arg-type]


@router.post(
    "",
    response_model=ProductDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
    description="Create a new product. Admin access required.",
    dependencies=[AdminRoleDep],
)
async def create_product(data: ProductCreate, product_service: ProductServiceDep) -> ProductDetail:
    """Create a new product."""
    product = await product_service.create_product(data)
    return ProductDetail(
        **product.model_dump(),
        review_count=await product_service.get_product_review_count(product.id),
        average_rating=await product_service.get_product_average_rating(product.id),
    )


@router.get(
    "/id/{product_id}",
    response_model=ProductDetail,
    summary="Get product by ID",
    description="Retrieve detailed information about a specific product using its UUID.",
)
async def get_product_by_id(product_id: UUID, product_service: ProductServiceDep) -> ProductDetail:
    """Retrieve a product by its ID."""
    product = await product_service.get_product_by_id(product_id)
    return ProductDetail(
        **product.model_dump(),
        review_count=await product_service.get_product_review_count(product_id),
        average_rating=await product_service.get_product_average_rating(product_id),
    )


@router.get(
    "/slug/{slug}",
    response_model=ProductDetail,
    summary="Get product by slug",
    description="Retrieve detailed information about a specific product using its URL-friendly slug.",
)
async def get_product_by_slug(slug: str, product_service: ProductServiceDep) -> ProductDetail:
    """Retrieve a product by its slug."""
    product = await product_service.get_product_by_slug(slug)
    return ProductDetail(
        **product.model_dump(),
        review_count=await product_service.get_product_review_count(product.id),
        average_rating=await product_service.get_product_average_rating(product.id),
    )


@router.patch(
    "/{product_id}",
    response_model=ProductDetail,
    summary="Update product",
    description="Update an existing product's information. Admin access required.",
    dependencies=[AdminRoleDep],
)
async def update_product(
    product_id: UUID, data: ProductUpdate, product_service: ProductServiceDep
) -> ProductDetail:
    """Update a product by its ID."""
    product = await product_service.update_product(product_id, data)
    return ProductDetail(
        **product.model_dump(),
        review_count=await product_service.get_product_review_count(product_id),
        average_rating=await product_service.get_product_average_rating(product_id),
    )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
    description="Permanently delete a product from the catalog. Admin access required. This action cannot be undone.",
    dependencies=[AdminRoleDep],
)
async def delete_product(product_id: UUID, product_service: ProductServiceDep) -> None:
    """Delete a product by its ID."""
    await product_service.delete_product(product_id)
