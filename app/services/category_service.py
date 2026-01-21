"""Service layer for Category operations."""

# mypy: disable-error-code=return-value
from uuid import UUID

from pydantic import HttpUrl

from app.core.exceptions import CategoryNotFoundError, SelfReferenceError
from app.core.logger import logger
from app.interfaces.unit_of_work import UnitOfWork
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    """Service class for managing categories."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def get_categories(self) -> list[Category]:
        """List all categories.

        Returns:
            list[Category]: A list of all categories.
        """
        return await self.uow.categories.list_all()

    async def get_category_by_id(
        self,
        category_id: UUID,
    ) -> Category:
        """Get a category by its ID.

        Args:
            category_id (UUID): The ID of the category to find.

        Returns:
            Category: The category with the specified ID.

        Raises:
            CategoryNotFoundError: If the category is not found.
        """
        category = await self.uow.categories.find_by_id(category_id)
        if not category:
            raise CategoryNotFoundError(category_id)
        return category

    async def get_category_by_slug(
        self,
        slug: str,
    ) -> Category:
        """Get a category by its slug.

        Args:
            slug (str): The slug of the category to find.

        Returns:
            Category: The category with the specified slug.

        Raises:
            CategoryNotFoundError: If the category is not found.
        """
        category = await self.uow.categories.find_by_slug(slug)
        if not category:
            raise CategoryNotFoundError(slug=slug)
        return category

    async def create_category(
        self,
        data: CategoryCreate,
    ) -> Category:
        """Create a new category.

        Args:
            data (CategoryCreate): The data for the new category.

        Returns:
            Category: The newly created category.

        Raises:
            CategoryNotFoundError: If the parent category does not exist.
        """
        if data.parent_id:
            # Ensure the parent category exists
            _ = await self.get_category_by_id(data.parent_id)

        slug = await self.uow.categories.generate_slug(data.name)

        category_data = data.model_dump()
        if isinstance(category_data.get("image_url"), HttpUrl):
            category_data["image_url"] = str(category_data["image_url"])

        new_category = Category(slug=slug, **category_data)
        created_category = await self.uow.categories.add(new_category)
        logger.info(
            "category_created", category_id=str(created_category.id), name=created_category.name
        )
        return created_category

    async def update_category(
        self,
        category_id: UUID,
        data: CategoryUpdate,
    ) -> Category:
        """Update an existing category.

        Args:
            category_id (UUID): The ID of the category to update.
            data (CategoryUpdate): The updated data for the category.

        Returns:
            Category: The updated category.

        Raises:
            CategoryNotFoundError: If the category or new parent category does not exist.
            SelfReferenceError: If trying to set itself as parent.
        """
        category = await self.get_category_by_id(category_id)

        if data.parent_id:
            # Prevent setting itself as parent
            if data.parent_id == category_id:
                raise SelfReferenceError(entity="Category", field="parent")
            # Ensure the new parent category exists
            _ = await self.get_category_by_id(data.parent_id)

        category_data = data.model_dump(exclude_unset=True)

        if isinstance(category_data.get("image_url"), HttpUrl):
            category_data["image_url"] = str(category_data["image_url"])

        for key, value in category_data.items():
            setattr(category, key, value)

        updated_category = await self.uow.categories.update(category)
        logger.info("category_updated", category_id=str(category_id))
        return updated_category

    async def delete_category(
        self,
        category_id: UUID,
    ) -> None:
        """Delete a category by its ID.

        Args:
            category_id (UUID): The ID of the category to delete.

        Raises:
            CategoryNotFoundError: If the category is not found.
        """
        category = await self.get_category_by_id(category_id)
        await self.uow.categories.delete(category)
        logger.info("category_deleted", category_id=str(category_id))
