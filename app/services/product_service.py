"""Service layer for product-related operations."""

from uuid import UUID

from fastapi import HTTPException
from pydantic import HttpUrl

from app.interfaces.unit_of_work import UnitOfWork
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.utils.sku import generate_sku


class ProductService:
    """Service class for product-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def list_all(
        self,
        *,
        page: int = 1,
        per_page: int = 10,
        search: str | None = None,
        category_id: UUID | None = None,
        category_slug: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
        availability: str = "all",
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Product], int]:
        """List all products with optional filters, sorting, and pagination.

        Args:
            page (int, optional): Page number for pagination.
            per_page (int, optional): Number of items per page for pagination.
            search (str | None): Search query to filter products by name or description.
            category_id (UUID | None): Category ID to filter products.
            category_slug (str | None): Category slug to filter products.
            min_price (float | None): Minimum price to filter products.
            max_price (float | None): Maximum price to filter products.
            min_rating (float | None): Minimum average rating to filter products.
            availability (str, optional): Stock availability filter ("in_stock", "out_of_stock", "all").
            sort_by (str, optional): Field to sort by (e.g., "price", "name", "rating").
            sort_order (str, optional): Sort order ("asc" or "desc").

        Returns:
            tuple[list[Product], int]: A list of products and the total number of items.

        Raises:
            HTTPException: If the category does not exist.
        """
        if category_id:
            category = await self.uow.categories.find_by_id(category_id)
            if not category:
                raise HTTPException(status_code=404, detail="Category not found.")

        if category_slug:
            category = await self.uow.categories.find_by_slug(category_slug)
            if not category:
                raise HTTPException(status_code=404, detail="Category not found.")

        products, total = await self.uow.products.paginate(
            page=page,
            per_page=per_page,
            search=search,
            category_id=category_id,
            category_slug=category_slug,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            availability=availability,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return products, total

    async def list_autocomplete_suggestions(self, query: str, limit: int = 10) -> list[str]:
        """List autocomplete suggestions for product names based on a search query.

        Args:
            query (str): The search query string.
            limit (int, optional): The maximum number of suggestions to return. Defaults to 10.

        Returns:
            list[str]: Autocomplete suggestions for product names.

        Raises:
            HTTPException: If the query is less than 2 characters long.
        """
        if not query or len(query) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters long.")
        return await self.uow.products.list_autocomplete_suggestions(query, limit)

    async def find_by_id(
        self,
        product_id: UUID,
    ) -> Product:
        """Find a product by its ID.

        Args:
            product_id (UUID): The ID of the product to find.

        Returns:
            Product: The product with the specified ID.

        Raises:
            HTTPException: If the product is not found.
        """
        product = await self.uow.products.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
        return product

    async def calculate_average_rating(self, product_id: UUID) -> float | None:
        """Calculate the average rating for a product.

        Args:
            product_id (UUID): The ID of the product.

        Returns:
            float | None: The average rating of the product, or None if no ratings exist.
        """
        return await self.uow.products.calculate_average_rating(product_id)

    async def count_reviews(self, product_id: UUID) -> int:
        """Count the total number of reviews for a product.

        Args:
            product_id (UUID): The ID of the product.

        Returns:
            int: The total number of reviews for the product.
        """
        return await self.uow.products.count_reviews(product_id)

    async def find_by_slug(
        self,
        slug: str,
    ) -> Product:
        """Find a product by its slug.

        Args:
            slug (str): The slug of the product to find.

        Returns:
            Product: The product with the specified slug.

        Raises:
            HTTPException: If the product is not found.
        """
        product = await self.uow.products.find_by_slug(slug)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
        return product

    async def create(
        self,
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
        # Validate category existence if category_id is provided
        if data.category_id:
            category = await self.uow.categories.find_by_id(data.category_id)
            if not category:
                raise HTTPException(status_code=404, detail="Category not found.")

        slug = await self.uow.products.generate_slug(data.name)
        sku = generate_sku(data.name)

        product_data = data.model_dump(exclude_unset=True)
        if isinstance(product_data.get("image_url"), HttpUrl):
            product_data["image_url"] = str(product_data["image_url"])

        new_product = Product(slug=slug, sku=sku, **product_data)

        return await self.uow.products.add(new_product)

    async def update(
        self,
        product_id: UUID,
        data: ProductUpdate,
    ) -> Product:
        """Update an existing product.

        Args:
            product_id (UUID): The ID of the product to update.
            data (ProductUpdate): The updated product data.

        Returns:
            Product: The updated product.

        Raises:
            HTTPException: If the product or category does not exist.
        """
        product = await self.uow.products.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        # Validate category existence if category_id is provided
        if data.category_id:
            category = await self.uow.categories.find_by_id(data.category_id)
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
        product = await self.uow.products.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
        await self.uow.products.delete(product)
