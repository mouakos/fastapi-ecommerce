"""Service layer for Category operations."""

from uuid import UUID

from fastapi import HTTPException
from pydantic import HttpUrl
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.utils.slug import generate_slug


class CategoryService:
    """Service class for managing categories."""

    @staticmethod
    async def list_all(
        session: AsyncSession,
    ) -> list[Category]:
        """List all categories.

        Args:
            session (AsyncSession): The database session.

        Returns:
            list[Category]: A list of all categories.
        """
        stmt = select(Category)
        result = await session.exec(stmt)
        return list(result.all())

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        category_id: UUID,
    ) -> Category:
        """Retrieve a category by its ID.

        Args:
            session (AsyncSession): The database session.
            category_id (UUID): The ID of the category to retrieve.

        Returns:
            Category: The category with the specified ID.

        Raises:
            HTTPException: If the category is not found.
        """
        stmt = select(Category).where(Category.id == category_id)
        category = (await session.exec(stmt)).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")
        return category

    @staticmethod
    async def get_by_slug(
        session: AsyncSession,
        slug: str,
    ) -> Category:
        """Retrieve a category by its slug.

        Args:
            session (AsyncSession): The database session.
            slug (str): The slug of the category to retrieve.

        Returns:
            Category: The category with the specified slug.

        Raises:
            HTTPException: If the category is not found.
        """
        stmt = select(Category).where(Category.slug == slug)
        category = (await session.exec(stmt)).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")
        return category

    @staticmethod
    async def create(
        session: AsyncSession,
        data: CategoryCreate,
    ) -> Category:
        """Create a new category.

        Args:
            session (AsyncSession): The database session.
            data (CategoryCreate): The data for the new category.

        Returns:
            Category: The newly created category.

        Raises:
            HTTPException: If the parent category does not exist.
        """
        slug = await generate_slug(session, data.name)

        category_data = data.model_dump()
        if isinstance(category_data.get("image_url"), HttpUrl):
            category_data["image_url"] = str(category_data["image_url"])

        new_category = Category(slug=slug, **category_data)
        session.add(new_category)
        await session.flush()
        await session.refresh(new_category)
        return new_category

    @staticmethod
    async def update(
        session: AsyncSession,
        category_id: UUID,
        data: CategoryUpdate,
    ) -> Category:
        """Update an existing category.

        Args:
            session (AsyncSession): The database session.
            category_id (UUID): The ID of the category to update.
            data (CategoryUpdate): The updated data for the category.

        Returns:
            Category: The updated category.

        Raises:
            HTTPException: If the category or new parent category does not exist, or if trying to set itself as parent.
        """
        category = await CategoryService.get_by_id(session, category_id)

        if data.parent_id:
            # Prevent setting itself as parent
            if data.parent_id == category_id:
                raise HTTPException(
                    status_code=400,
                    detail="Category cannot be its own parent.",
                )
            # Ensure the new parent category exists
            _ = await CategoryService.get_by_id(session, data.parent_id)

        category_data = data.model_dump(exclude_unset=True)

        if isinstance(category_data.get("image_url"), HttpUrl):
            category_data["image_url"] = str(category_data["image_url"])

        for key, value in category_data.items():
            setattr(category, key, value)

        await session.flush()
        await session.refresh(category)
        return category

    @staticmethod
    async def delete(
        session: AsyncSession,
        category_id: UUID,
    ) -> None:
        """Delete a category by its ID.

        Args:
            session (AsyncSession): The database session.
            category_id (UUID): The ID of the category to delete.

        Raises:
            HTTPException: If the category is not found.
        """
        category = await CategoryService.get_by_id(session, category_id)
        await session.delete(category)
        await session.flush()
