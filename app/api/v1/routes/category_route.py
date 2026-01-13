"""Category API routes."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.v1.dependencies import AdminRoleDep, CategoryServiceDep
from app.schemas.category_schema import CategoryCreate, CategoryRead, CategoryUpdate

category_router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])


@category_router.get(
    "/",
    response_model=list[CategoryRead],
)
async def list_categories(
    category_service: CategoryServiceDep,
) -> list[CategoryRead]:
    """List all categories."""
    return await category_service.list_all()


@category_router.post(
    "/",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
    dependencies=[AdminRoleDep],
)
async def create_category(
    data: CategoryCreate, category_service: CategoryServiceDep
) -> CategoryRead:
    """Create a new category."""
    return await category_service.create(data)


@category_router.get(
    "/id/{category_id}",
    response_model=CategoryRead,
    summary="Retrieve a category by its ID",
)
async def get_category(category_id: UUID, category_service: CategoryServiceDep) -> CategoryRead:
    """Retrieve a category by its ID."""
    return await category_service.get_by_id(category_id)


@category_router.get(
    "/slug/{slug}",
    response_model=CategoryRead,
    summary="Retrieve a category by its slug",
)
async def get_category_by_slug(slug: str, category_service: CategoryServiceDep) -> CategoryRead:
    """Retrieve a category by its slug."""
    return await category_service.get_by_slug(slug)


@category_router.put(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Update a category by its ID",
    dependencies=[AdminRoleDep],
)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    category_service: CategoryServiceDep,
) -> CategoryRead:
    """Update a category by its ID."""
    return await category_service.update(category_id, data)


@category_router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category by its ID",
    dependencies=[AdminRoleDep],
)
async def delete_category(category_id: UUID, category_service: CategoryServiceDep) -> None:
    """Delete a category by its ID."""
    return await category_service.delete(category_id)
