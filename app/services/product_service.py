"""Service layer for product-related operations."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import HTTPException
from pydantic import HttpUrl

from app.interfaces.unit_of_work import UnitOfWork
from app.models.product import Product
from app.schemas.product_schema import ProductCreate, ProductRead, ProductUpdate
from app.utils.sku import generate_sku


class ProductService:
    """Service class for product-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def list_all(self) -> list[ProductRead]:
        """List all products.

        Args:
            session (AsyncSession): The database session.

        Returns:
            list[ProductRead]: A list of all products.
        """
        return await self.uow.products.list_all()

    async def get_by_id(
        self,
        product_id: UUID,
    ) -> ProductRead:
        """Retrieve a product by its ID.

        Args:
            session (AsyncSession): The database session.
            product_id (UUID): The ID of the product to retrieve.

        Returns:
            ProductRead: The product with the specified ID.

        Raises:
            HTTPException: If the product is not found.
        """
        product = await self.uow.products.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
        return product

    async def get_by_slug(
        self,
        slug: str,
    ) -> ProductRead:
        """Retrieve a product by its slug.

        Args:
            slug (str): The slug of the product to retrieve.

        Returns:
            ProductRead: The product with the specified slug.

        Raises:
            HTTPException: If the product is not found.
        """
        product = await self.uow.products.get_by_slug(slug)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
        return product

    async def create(
        self,
        data: ProductCreate,
    ) -> ProductRead:
        """Create a new product.

        Args:
            session (AsyncSession): The database session.
            data (ProductCreate): The product data.

        Returns:
            ProductRead: The created product.

        Raises:
            HTTPException: If the category does not exist.
        """
        # Validate category existence if category_id is provided
        if data.category_id:
            category = await self.uow.categories.get_by_id(data.category_id)
            if not category:
                raise HTTPException(status_code=404, detail="Category not found.")

        slug = await self.uow.products.generate_slug(data.name)
        sku = generate_sku(data.name)

        product_data = data.model_dump()
        if isinstance(product_data.get("image_url"), HttpUrl):
            product_data["image_url"] = str(product_data["image_url"])

        new_product = Product(slug=slug, sku=sku, **product_data)

        return await self.uow.products.add(new_product)

    async def update(
        self,
        product_id: UUID,
        data: ProductUpdate,
    ) -> ProductRead:
        """Update an existing product.

        Args:
            product_id (UUID): The ID of the product to update.
            data (ProductUpdate): The updated product data.

        Returns:
            ProductRead: The updated product.

        Raises:
            HTTPException: If the product or category does not exist.
        """
        product = await self.uow.products.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        # Validate category existence if category_id is provided
        if data.category_id:
            category = await self.uow.categories.get_by_id(data.category_id)
            if not category:
                raise HTTPException(status_code=404, detail="Category not found.")

        product_data = data.model_dump(exclude_unset=True)
        if isinstance(product_data.get("image_url"), HttpUrl):
            product_data["image_url"] = str(product_data["image_url"])

        for key, value in product_data.items():
            setattr(product, key, value)

        return await self.uow.products.update(product)

    async def delete(
        self,
        product_id: UUID,
    ) -> None:
        """Delete a product by its ID.

        Args:
            product_id (UUID): The ID of the product to delete.

        Raises:
            HTTPException: If the product does not exist.
        """
        product = await self.get_by_id(product_id)
        await self.uow.products.delete(product.id)
