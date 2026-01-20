"""Service layer for product-related operations."""

from decimal import Decimal
from uuid import UUID

from pydantic import HttpUrl

from app.core.exceptions import CategoryNotFoundError, ProductNotFoundError
from app.interfaces.unit_of_work import UnitOfWork
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.utils.product import generate_sku


class ProductService:
    """Service class for product-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def get_products(
        self,
        *,
        search: str | None = None,
        category_id: UUID | None = None,
        category_slug: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        min_rating: float | None = None,
        availability: str = "all",
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Product], int]:
        """Get all active products with optional filters, sorting, and pagination.

        Args:
            search (str | None): Search query to filter by name or description. Defaults to None.
            category_id (UUID | None): Filter by category ID. Defaults to None.
            category_slug (str | None): Filter by category slug. Defaults to None.
            min_price (Decimal | None): Minimum price filter. Defaults to None.
            max_price (Decimal | None): Maximum price filter. Defaults to None.
            min_rating (float | None): Minimum average rating filter. Defaults to None.
            availability (str): Stock filter ("in_stock", "out_of_stock", "all"). Defaults to "all".
            sort_by (str): Field to sort by. Defaults to "created_at".
            sort_order (str): Sort order ("asc" or "desc"). Defaults to "desc".
            page (int): Page number for pagination. Defaults to 1.
            page_size (int): Items per page. Defaults to 10.

        Returns:
            tuple[list[Product], int]: List of active products and total count.
        """
        products, total = await self.uow.products.find_all(
            page=page,
            page_size=page_size,
            search=search,
            category_id=category_id,
            category_slug=category_slug,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            is_active=True,
            availability=availability,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return products, total

    async def get_autocomplete_suggestions(self, query: str, limit: int = 10) -> list[str]:
        """Get autocomplete suggestions for product names based on a search query.

        Args:
            query (str): The search query string.
            limit (int, optional): The maximum number of suggestions to return. Defaults to 10.

        Returns:
            list[str]: Autocomplete suggestions for product names.
        """
        return await self.uow.products.list_autocomplete_suggestions(query, limit)

    async def get_product_by_id(
        self,
        product_id: UUID,
    ) -> Product:
        """Get a product by its ID.

        Args:
            product_id (UUID): The ID of the product to find.

        Returns:
            Product: The product with the specified ID.

        Raises:
            ProductNotFoundError: If the product is not found.
        """
        product = await self.uow.products.find_active_by_id(product_id)
        if not product:
            raise ProductNotFoundError(product_id=product_id)
        return product

    async def get_product_average_rating(self, product_id: UUID) -> float | None:
        """Get the average rating for a product.

        Args:
            product_id (UUID): The ID of the product.

        Returns:
            float | None: The average rating of the product, or None if no ratings exist.
        """
        return await self.uow.products.calculate_average_rating(product_id)

    async def get_product_review_count(self, product_id: UUID) -> int:
        """Get the total number of reviews for a product.

        Args:
            product_id (UUID): The ID of the product.

        Returns:
            int: The total number of reviews for the product.
        """
        return await self.uow.products.count_reviews(product_id)

    async def get_product_by_slug(
        self,
        slug: str,
    ) -> Product:
        """Get a product by its slug.

        Args:
            slug (str): The slug of the product to find.

        Returns:
            Product: The product with the specified slug.

        Raises:
            ProductNotFoundError: If the product is not found.
        """
        product = await self.uow.products.find_active_by_slug(slug)
        if not product:
            raise ProductNotFoundError(slug=slug)

        return product

    async def create_product(
        self,
        data: ProductCreate,
    ) -> Product:
        """Create a new product with auto-generated slug and SKU.

        Args:
            data (ProductCreate): Product data including name, price, stock, and category.

        Returns:
            Product: The created product.

        Raises:
            CategoryNotFoundError: If the specified category does not exist.
        """
        # Validate category existence if category_id is provided
        if data.category_id:
            category = await self.uow.categories.find_by_id(data.category_id)
            if not category:
                raise CategoryNotFoundError(category_id=data.category_id)

        slug = await self.uow.products.generate_slug(data.name)
        sku = generate_sku(data.name)

        product_data = data.model_dump(exclude_unset=True)
        if isinstance(product_data.get("image_url"), HttpUrl):
            product_data["image_url"] = str(product_data["image_url"])

        new_product = Product(slug=slug, sku=sku, **product_data)

        return await self.uow.products.add(new_product)

    async def update_product(
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
            ProductNotFoundError: If the product is not found.
            CategoryNotFoundError: If the specified category does not exist.
        """
        product = await self.get_product_by_id(product_id)

        # Validate category existence if category_id is provided
        if data.category_id:
            category = await self.uow.categories.find_by_id(data.category_id)
            if not category:
                raise CategoryNotFoundError(category_id=data.category_id)

        product_data = data.model_dump(exclude_unset=True)
        if isinstance(product_data.get("image_url"), HttpUrl):
            product_data["image_url"] = str(product_data["image_url"])

        for key, value in product_data.items():
            setattr(product, key, value)

        return await self.uow.products.update(product)

    async def delete_product(
        self,
        product_id: UUID,
    ) -> None:
        """Delete a product by its ID.

        Args:
            product_id (UUID): The ID of the product to delete.

        Raises:
            ProductNotFoundError: If the product is not found.
        """
        product = await self.get_product_by_id(product_id)
        await self.uow.products.delete(product)
