"""Category API routes."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.v1.dependencies import AdminRoleDep, CategoryServiceDep
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["Categories"])


# Collection paths
@router.get(
    "",
    response_model=list[CategoryRead],
    summary="List categories",
    description="Retrieve all product categories with their hierarchy information.",
)
async def list_categories(
    category_service: CategoryServiceDep,
) -> list[CategoryRead]:
    """List all categories."""
    return await category_service.list_all()


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
    description="Create a new product category. Admin access required.",
    dependencies=[AdminRoleDep],
)
async def create_category(
    data: CategoryCreate, category_service: CategoryServiceDep
) -> CategoryRead:
    """Create a new category."""
    return await category_service.create(data)


# Specific lookup paths (before parameterized paths)
@router.get(
    "/id/{category_id}",
    response_model=CategoryRead,
    summary="Get category by ID",
    description="Retrieve a specific category using its UUID.",
)
async def get_category(category_id: UUID, category_service: CategoryServiceDep) -> CategoryRead:
    """Retrieve a category by its ID."""
    return await category_service.get_by_id(category_id)


@router.get(
    "/slug/{slug}",
    response_model=CategoryRead,
    summary="Get category by slug",
    description="Retrieve a specific category using its URL-friendly slug.",
)
async def get_category_by_slug(slug: str, category_service: CategoryServiceDep) -> CategoryRead:
    """Retrieve a category by its slug."""
    return await category_service.get_by_slug(slug)


# Parameterized admin operations
@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Update category",
    description="Update an existing category's information. Admin access required.",
    dependencies=[AdminRoleDep],
)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    category_service: CategoryServiceDep,
) -> CategoryRead:
    """Update a category by its ID."""
    return await category_service.update(category_id, data)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category",
    description="Permanently delete a category. Admin access required. This action cannot be undone.",
    dependencies=[AdminRoleDep],
)
async def delete_category(category_id: UUID, category_service: CategoryServiceDep) -> None:
    """Delete a category by its ID."""
    return await category_service.delete(category_id)
