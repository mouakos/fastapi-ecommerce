"""Service layer for product-related operations."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import HTTPException
from pydantic import HttpUrl

from app.interfaces.unit_of_work import UnitOfWork
from app.models.product import Product
from app.schemas.common import PaginatedRead, PaginationLinks, PaginationMeta
from app.schemas.product import ProductCreate, ProductDetailRead, ProductRead, ProductUpdate
from app.schemas.search import (
    AvailabilityFilter,
    ProductAutocompleteRead,
    SortByField,
    SortOrder,
)
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
        total_items, products = await self.uow.products.list_all_paginated(
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

        total_pages = (total_items + per_page - 1) // per_page
        from_item = (page - 1) * per_page + 1 if total_items > 0 else 0
        to_item = min(page * per_page, total_items)

        meta = PaginationMeta(
            current_page=page,
            per_page=per_page,
            total_pages=total_pages,
            total_items=total_items,
            from_item=from_item,
            to_item=to_item,
        )

        # Build query string for HATEOAS links
        base = "/products?"
        query_params = []
        if search:
            query_params.append(f"search={search}")
        if category_id is not None:
            query_params.append(f"category_id={category_id}")
        if min_price is not None:
            query_params.append(f"min_price={min_price}")
        if max_price is not None:
            query_params.append(f"max_price={max_price}")
        if min_rating is not None:
            query_params.append(f"min_rating={min_rating}")
        if availability != AvailabilityFilter.ALL:
            query_params.append(f"availability={availability.value}")
        if sort_by != SortByField.ID:
            query_params.append(f"sort_by={sort_by.value}")
        if sort_order != SortOrder.ASC:
            query_params.append(f"sort_order={sort_order.value}")

        query_string = "&".join(query_params)
        base += query_string + "&" if query_string else ""

        links = PaginationLinks(
            self=f"{base}page={page}&per_page={per_page}",
            first=f"{base}page=1&per_page={per_page}",
            prev=f"{base}page={page - 1}&per_page={per_page}" if page > 1 else None,
            next=f"{base}page={page + 1}&per_page={per_page}" if page < total_pages else None,
            last=f"{base}page={total_pages}&per_page={per_page}",
        )

        return PaginatedRead[Product](data=products, meta=meta, links=links)

    async def get_autocomplete_suggestions(
        self, query: str, limit: int = 10
    ) -> ProductAutocompleteRead:
        """Get autocomplete suggestions for product names based on a search query.

        Args:
            query (str): The search query string.
            limit (int, optional): The maximum number of suggestions to return. Defaults to 10.

        Returns:
            ProductAutocompleteRead: Autocomplete suggestions for product names.

        Raises:
            HTTPException: If the query is less than 2 characters long.
        """
        if not query or len(query) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters long.")
        suggestions = await self.uow.products.get_autocomplete_suggestions(query, limit)
        return ProductAutocompleteRead(suggestions=suggestions)

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

    async def get_by_category_slug(
        self,
        category_slug: str,
    ) -> list[ProductRead]:
        """Retrieve products by category slug.

        Args:
            category_slug (str): The slug of the category.

        Returns:
            list[ProductRead]: List of products in the specified category.

        Raises:
            HTTPException: If the category is not found.
        """
        category = await self.uow.categories.get_by_slug(category_slug)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")

        return await self.uow.products.get_by_category_slug(category.slug)

    async def get_by_category_id(
        self,
        category_id: UUID,
    ) -> list[ProductRead]:
        """Retrieve products by category ID.

        Args:
            category_id (UUID): The ID of the category.

        Returns:
            list[ProductRead]: List of products in the specified category.

        Raises:
            HTTPException: If the category is not found.
        """
        category = await self.uow.categories.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")

        return await self.uow.products.get_by_category_id(category.id)

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
