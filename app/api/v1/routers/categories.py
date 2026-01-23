"""Product category management API routes with hierarchical support."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import APIRouter, status

from app.api.cache import cache
from app.api.v1.dependencies import AdminRoleDep, CategoryServiceDep
from app.schemas.category import CategoryCreate, CategoryPublic, CategoryUpdate

router = APIRouter()


@router.get(
    "",
    response_model=list[CategoryPublic],
    summary="Get all categories",
    description="Retrieve all product categories with their hierarchy information.",
)
@cache(expire=1800)
async def get_categories(
    category_service: CategoryServiceDep,
) -> list[CategoryPublic]:
    """Get all categories."""
    return await category_service.get_categories()


@router.post(
    "",
    response_model=CategoryPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
    description="Create a new product category. Admin access required.",
    dependencies=[AdminRoleDep],
)
async def create_category(
    data: CategoryCreate, category_service: CategoryServiceDep
) -> CategoryPublic:
    """Create a new category."""
    return await category_service.create_category(data)


@router.get(
    "/id/{category_id}",
    response_model=CategoryPublic,
    summary="Get category by ID",
    description="Retrieve a specific category using its UUID.",
)
@cache(expire=600)
async def get_category_by_id(
    category_id: UUID, category_service: CategoryServiceDep
) -> CategoryPublic:
    """Get a category by its ID."""
    return await category_service.get_category_by_id(category_id)


@router.get(
    "/slug/{slug}",
    response_model=CategoryPublic,
    summary="Get category by slug",
    description="Retrieve a specific category using its URL-friendly slug.",
)
@cache(expire=600)
async def get_category_by_slug(slug: str, category_service: CategoryServiceDep) -> CategoryPublic:
    """Get a category by its slug."""
    return await category_service.get_category_by_slug(slug)


@router.patch(
    "/{category_id}",
    response_model=CategoryPublic,
    summary="Update category",
    description="Update an existing category's information. Admin access required.",
    dependencies=[AdminRoleDep],
)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    category_service: CategoryServiceDep,
) -> CategoryPublic:
    """Update a category by its ID."""
    return await category_service.update_category(category_id, data)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category",
    description="Permanently delete a category. Admin access required. This action cannot be undone.",
    dependencies=[AdminRoleDep],
)
async def delete_category(category_id: UUID, category_service: CategoryServiceDep) -> None:
    """Delete a category by its ID."""
    return await category_service.delete_category(category_id)
