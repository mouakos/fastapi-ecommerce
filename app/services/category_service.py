"""Service layer for Category operations."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import HTTPException
from pydantic import HttpUrl

from app.interfaces.unit_of_work import UnitOfWork
from app.models.category import Category
from app.schemas.category_schema import CategoryCreate, CategoryRead, CategoryUpdate


class CategoryService:
    """Service class for managing categories."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def list_all(self) -> list[CategoryRead]:
        """List all categories.

        Returns:
            list[CategoryRead]: A list of all categories.
        """
        return await self.uow.categories.list_all()

    async def get_by_id(
        self,
        category_id: UUID,
    ) -> CategoryRead:
        """Retrieve a category by its ID.

        Args:
            category_id (UUID): The ID of the category to retrieve.

        Returns:
            CategoryRead: The category with the specified ID.

        Raises:
            HTTPException: If the category is not found.
        """
        category = await self.uow.categories.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")
        return category

    async def get_by_slug(
        self,
        slug: str,
    ) -> CategoryRead:
        """Retrieve a category by its slug.

        Args:
            session (AsyncSession): The database session.
            slug (str): The slug of the category to retrieve.

        Returns:
            CategoryRead: The category with the specified slug.

        Raises:
            HTTPException: If the category is not found.
        """
        category = await self.uow.categories.get_by_slug(slug)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")
        return category

    async def create(
        self,
        data: CategoryCreate,
    ) -> CategoryRead:
        """Create a new category.

        Args:
            data (CategoryCreate): The data for the new category.

        Returns:
            CategoryRead: The newly created category.

        Raises:
            HTTPException: If the parent category does not exist.
        """
        if data.parent_id:
            # Ensure the parent category exists
            _ = await self.get_by_id(data.parent_id)

        slug = await self.uow.categories.generate_slug(data.name)

        category_data = data.model_dump()
        if isinstance(category_data.get("image_url"), HttpUrl):
            category_data["image_url"] = str(category_data["image_url"])

        new_category = Category(slug=slug, **category_data)
        return await self.uow.categories.add(new_category)

    async def update(
        self,
        category_id: UUID,
        data: CategoryUpdate,
    ) -> CategoryRead:
        """Update an existing category.

        Args:
            category_id (UUID): The ID of the category to update.
            data (CategoryUpdate): The updated data for the category.

        Returns:
            CategoryRead: The updated category.

        Raises:
            HTTPException: If the category or new parent category does not exist, or if trying to set itself as parent.
        """
        category = await self.uow.categories.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")

        if data.parent_id:
            # Prevent setting itself as parent
            if data.parent_id == category_id:
                raise HTTPException(
                    status_code=400,
                    detail="Category cannot be its own parent.",
                )
            # Ensure the new parent category exists
            _ = await self.get_by_id(data.parent_id)

        category_data = data.model_dump(exclude_unset=True)

        if isinstance(category_data.get("image_url"), HttpUrl):
            category_data["image_url"] = str(category_data["image_url"])

        for key, value in category_data.items():
            setattr(category, key, value)

        return await self.uow.categories.update(category)

    async def delete(
        self,
        category_id: UUID,
    ) -> None:
        """Delete a category by its ID.

        Args:
            category_id (UUID): The ID of the category to delete.

        Raises:
            HTTPException: If the category is not found.
        """
        if not await self.uow.categories.delete_by_id(category_id):
            raise HTTPException(status_code=404, detail="Category not found.")
