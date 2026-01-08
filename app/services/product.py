"""Service layer for product-related operations."""

from uuid import UUID

from fastapi import HTTPException
from pydantic import HttpUrl
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.category import CategoryService
from app.utils.sku import generate_sku
from app.utils.slug import generate_slug


class ProductService:
    """Service class for product-related operations."""

    @staticmethod
    async def list_all(
        session: AsyncSession,
    ) -> list[Product]:
        """List all products.

        Args:
            session (AsyncSession): The database session.

        Returns:
            list[Product]: A list of all products.
        """
        stmt = select(Product)
        result = await session.exec(stmt)
        return list(result.all())

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        product_id: UUID,
    ) -> Product:
        """Retrieve a product by its ID.

        Args:
            session (AsyncSession): The database session.
            product_id (UUID): The ID of the product to retrieve.

        Returns:
            Product: The product with the specified ID.

        Raises:
            HTTPException: If the product is not found.
        """
        product = await session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
        return product

    @staticmethod
    async def get_by_slug(
        session: AsyncSession,
        slug: str,
    ) -> Product:
        """Retrieve a product by its slug.

        Args:
            session (AsyncSession): The database session.
            slug (str): The slug of the product to retrieve.

        Returns:
            Product: The product with the specified slug.

        Raises:
            HTTPException: If the product is not found.
        """
        stmt = select(Product).where(Product.slug == slug)
        product = (await session.exec(stmt)).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
        return product

    @staticmethod
    async def create(
        session: AsyncSession,
        data: ProductCreate,
    ) -> Product:
        """Create a new product.

        Args:
            session (AsyncSession): The database session.
            data (ProductCreate): The product data.

        Returns:
            Product: The created product.

        Raises:
            HTTPException: If the category does not exist.
        """
        # Validate category existence
        _ = await CategoryService.get_by_id(session, data.category_id)

        slug = await generate_slug(session, data.name)
        sku = generate_sku(data.name)

        product_data = data.model_dump()
        if isinstance(product_data.get("image_url"), HttpUrl):
            product_data["image_url"] = str(product_data["image_url"])

        new_product = Product(slug=slug, sku=sku, **product_data)

        session.add(new_product)
        await session.flush()
        await session.refresh(new_product)
        return new_product

    @staticmethod
    async def update(
        session: AsyncSession,
        product_id: UUID,
        data: ProductUpdate,
    ) -> Product:
        """Update an existing product.

        Args:
            session (AsyncSession): The database session.
            product_id (UUID): The ID of the product to update.
            data (ProductUpdate): The updated product data.

        Returns:
            Product: The updated product.

        Raises:
            HTTPException: If the product or category does not exist.
        """
        product = await ProductService.get_by_id(session, product_id)

        # Validate category existence if category_id is provided
        if data.category_id:
            _ = CategoryService.get_by_id(session, data.category_id)

        product_data = data.model_dump(exclude_unset=True)
        if isinstance(product_data.get("image_url"), HttpUrl):
            product_data["image_url"] = str(product_data["image_url"])

        for key, value in product_data.items():
            setattr(product, key, value)

        await session.flush()
        await session.refresh(product)
        return product

    @staticmethod
    async def delete(
        session: AsyncSession,
        product_id: UUID,
    ) -> None:
        """Delete a product by its ID.

        Args:
            session (AsyncSession): The database session.
            product_id (UUID): The ID of the product to delete.

        Raises:
            HTTPException: If the product does not exist.
        """
        product = await ProductService.get_by_id(session, product_id)
        await session.delete(product)
        await session.flush()
