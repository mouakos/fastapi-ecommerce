"""Category API routes."""

# mypy: disable-error-code=return-value
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import get_session
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category import CategoryService

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])


@router.get(
    "/",
    response_model=list[CategoryRead],
)
async def list_categories(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[CategoryRead]:
    """List all categories."""
    return await CategoryService.list_all(session)


@router.post(
    "/",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
)
async def create_category(
    data: CategoryCreate, session: Annotated[AsyncSession, Depends(get_session)]
) -> CategoryRead:
    """Create a new category."""
    return await CategoryService.create(session, data)


@router.get(
    "/id/{category_id}",
    response_model=CategoryRead,
    summary="Retrieve a category by its ID",
)
async def get_category(
    category_id: UUID, session: Annotated[AsyncSession, Depends(get_session)]
) -> CategoryRead:
    """Retrieve a category by its ID."""
    return await CategoryService.get_by_id(session, category_id)


@router.get(
    "/slug/{slug}",
    response_model=CategoryRead,
    summary="Retrieve a category by its slug",
)
async def get_category_by_slug(
    slug: str, session: Annotated[AsyncSession, Depends(get_session)]
) -> CategoryRead:
    """Retrieve a category by its slug."""
    return await CategoryService.get_by_slug(session, slug)


@router.put(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Update a category by its ID",
)
async def update_category(
    category_id: UUID, data: CategoryUpdate, session: Annotated[AsyncSession, Depends(get_session)]
) -> CategoryRead:
    """Update a category by its ID."""
    return await CategoryService.update(session, category_id, data)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category by its ID",
)
async def delete_category(
    category_id: UUID, session: Annotated[AsyncSession, Depends(get_session)]
) -> None:
    """Delete a category by its ID."""
    return await CategoryService.delete(session, category_id)
