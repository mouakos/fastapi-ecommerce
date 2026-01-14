"""Service layer for product-related operations."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import HTTPException
from pydantic import HttpUrl

from app.interfaces.unit_of_work import UnitOfWork
from app.models.product import Product
from app.schemas.base import PaginatedRead
from app.schemas.product_schema import ProductCreate, ProductDetailRead, ProductRead, ProductUpdate
from app.schemas.search_schema import AvailabilityFilter, SortByField, SortOrder
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
        min_price: float | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
        availability: AvailabilityFilter = AvailabilityFilter.ALL,
        sort_by: SortByField = SortByField.ID,
        sort_order: SortOrder = SortOrder.ASC,
    ) -> PaginatedRead[ProductRead]:
        """List all products with optional filters, sorting, and pagination.

        Args:
            page (int, optional): Page number for pagination.
            per_page (int, optional): Number of items per page for pagination.
            search (str | None): Search query to filter products by name or description.
            category_id (int | None): Category ID to filter products.
            min_price (float | None): Minimum price to filter products.
            max_price (float | None): Maximum price to filter products.
            min_rating (float | None): Minimum average rating to filter products.
            availability (AvailabilityFilter, optional): Stock availability filter ("in_stock", "out_of_stock", "all").
            sort_by (SortByField, optional): Field to sort by (e.g., "price", "name", "rating").
            sort_order (SortOrder, optional): Sort order ("asc" or "desc").

        Returns:
            PaginatedRead[ProductRead]: A paginated list of all products.
        """
        return await self.uow.products.list_all_paginated(
            page=page,
            per_page=per_page,
            search=search,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            availability=availability.value,
            sort_by=sort_by.value,
            sort_order=sort_order.value,
        )

    async def get_by_id(
        self,
        product_id: UUID,
    ) -> ProductDetailRead:
        """Retrieve a product by its ID.

        Args:
            session (AsyncSession): The database session.
            product_id (UUID): The ID of the product to retrieve.

        Returns:
            ProductDetailRead: The product with the specified ID.

        Raises:
            HTTPException: If the product is not found.
        """
        product = await self.uow.products.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
        return await self._to_detail_read_model(product)

    async def get_by_slug(
        self,
        slug: str,
    ) -> ProductDetailRead:
        """Retrieve a product by its slug.

        Args:
            slug (str): The slug of the product to retrieve.

        Returns:
            ProductDetailRead: The product with the specified slug.

        Raises:
            HTTPException: If the product is not found.
        """
        product = await self.uow.products.get_by_slug(slug)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
        return await self._to_detail_read_model(product)

    async def create(
        self,
        data: ProductCreate,
    ) -> ProductDetailRead:
        """Create a new product.

        Args:
            session (AsyncSession): The database session.
            data (ProductCreate): The product data.

        Returns:
            ProductDetailRead: The created product.

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

        product = await self.uow.products.add(new_product)
        return await self._to_detail_read_model(product)

    async def update(
        self,
        product_id: UUID,
        data: ProductUpdate,
    ) -> ProductDetailRead:
        """Update an existing product.

        Args:
            product_id (UUID): The ID of the product to update.
            data (ProductUpdate): The updated product data.

        Returns:
            ProductDetailRead: The updated product.

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

        product = await self.uow.products.update(product)
        return await self._to_detail_read_model(product)

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
        if not await self.uow.products.delete_by_id(product_id):
            raise HTTPException(status_code=404, detail="Product not found.")

    async def _to_detail_read_model(self, product: Product) -> ProductDetailRead:
        """Convert a Product model to a ProductDetailRead schema.

        Args:
            product (Product): The product model.

        Returns:
            ProductDetailRead: The product read schema.
        """
        review_count = await self.uow.products.review_count(product.id)
        average_rating = await self.uow.products.average_rating(product.id)
        return ProductDetailRead(
            **product.model_dump(),
            review_count=review_count,
            average_rating=average_rating,
            in_stock=product.stock > 0,
        )
