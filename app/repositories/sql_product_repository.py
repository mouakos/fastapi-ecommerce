"""SQL Product repository implementation."""

from uuid import UUID

from slugify import slugify
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.product_repository import ProductRepository, allowed_sort_by, allowed_sort_order
from app.models.product import Product
from app.models.review import Review
from app.repositories.sql_generic_repository import SqlGenericRepository
from app.schemas.common import PaginatedRead, PaginationLinks, PaginationMeta


class SqlProductRepository(SqlGenericRepository[Product], ProductRepository):
    """SQL Product repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, Product)

    async def list_all_paginated(
        self,
        *,
        page: int = 1,
        per_page: int = 10,
        search: str | None = None,
        category_id: UUID | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
        availability: str = "all",
        sort_by: allowed_sort_by = "id",
        sort_order: allowed_sort_order = "asc",
    ) -> PaginatedRead[Product]:
        """Gets a list of products with optional filters, sorting, and pagination.

        Args:
            page (int, optional): Page number for pagination.
            per_page (int, optional): Number of items per page for pagination.
            search (str | None): Search query to filter products by name or description.
            category_id (int | None): Category ID to filter products.
            min_price (float | None): Minimum price to filter products.
            max_price (float | None): Maximum price to filter products.
            min_rating (float | None): Minimum average rating to filter products.
            availability (str | None): Stock availability filter ("in_stock", "out_of_stock", "all").
            sort_by (allowed_sort_by, optional): Field to sort by (e.g., "price", "name", "rating").
            sort_order (allowed_sort_order, optional): Sort order ("asc" or "desc").

        Returns:
            PaginatedRead[Product]: A paginated list of products.
        """
        page = max(page, 1)
        per_page = max(min(per_page, 100), 1)

        # Base query
        stmt = select(Product).where(Product.is_published)

        # Apply filters
        if search:
            search_term = f"%{search.lower()}%"
            stmt = stmt.where(
                (func.lower(Product.name).like(search_term))
                | (func.lower(Product.description).like(search_term))
            )
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)

        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)

        if availability == "in_stock":
            stmt = stmt.where(Product.stock > 0)
        elif availability == "out_of_stock":
            stmt = stmt.where(Product.stock == 0)

        if min_rating is not None:
            subquery = (
                select(Review.product_id, func.avg(Review.rating).label("avg_rating"))
                .group_by(Review.product_id)  # type: ignore [arg-type]
                .having(func.avg(Review.rating) >= min_rating)
                .subquery()
            )
            stmt = stmt.join(subquery, Product.id == subquery.c.product_id)  # type: ignore [arg-type]

        # Apply sorting
        sort_column = {
            "id": Product.id,
            "price": Product.price,
            "name": Product.name,
            "created_at": Product.created_at,
            "rating": func.coalesce(
                select(func.avg(Review.rating))
                .where(Review.product_id == Product.id)
                .correlate(Product)
                .scalar_subquery(),
                0,
            ),
            "popularity": func.coalesce(
                select(func.count(Review.id))  # type: ignore [arg-type]
                .where(Review.product_id == Product.id)
                .correlate(Product)
                .scalar_subquery(),
                0,
            ),
        }.get(sort_by, Product.id)
        sort_column = sort_column.desc() if sort_order == "desc" else sort_column.asc()  # type: ignore [attr-defined]
        stmt = stmt.order_by(sort_column)

        # total items matching filters
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_items = (await self._session.exec(count_stmt)).first() or 0

        # Apply pagination
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        result = await self._session.exec(stmt)
        items = list(result.all())

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
        if availability != "all":
            query_params.append(f"availability={availability}")
        if sort_by != "id":
            query_params.append(f"sort_by={sort_by}")
        if sort_order != "asc":
            query_params.append(f"sort_order={sort_order}")

        query_string = "&".join(query_params)
        base += query_string + "&" if query_string else ""

        links = PaginationLinks(
            self=f"{base}page={page}&per_page={per_page}",
            first=f"{base}page=1&per_page={per_page}",
            prev=f"{base}page={page - 1}&per_page={per_page}" if page > 1 else None,
            next=f"{base}page={page + 1}&per_page={per_page}" if page < total_pages else None,
            last=f"{base}page={total_pages}&per_page={per_page}",
        )

        return PaginatedRead[Product](data=items, meta=meta, links=links)

    async def get_by_slug(self, slug: str) -> Product | None:
        """Get a single product by slug.

        Args:
            slug (str): Product slug.

        Returns:
            Product | None: Product or none.
        """
        stmt = select(Product).where(Product.slug == slug)
        result = await self._session.exec(stmt)
        return result.first()

    async def generate_slug(self, name: str) -> str:
        """Generate a unique slug for a product based on its name.

        Args:
            name (str): Product name.

        Returns:
            str: Generated unique slug.
        """
        base_slug = slugify(name)
        slug = base_slug
        index = 1

        while True:
            stmt = select(Product).where(Product.slug == slug)
            result = await self._session.exec(stmt)
            product = result.first()

            if not product:
                return slug

            slug = f"{base_slug}-{index}"
            index += 1

    async def review_count(self, product_id: UUID) -> int:
        """Get the total number of reviews for a product.

        Args:
            product_id (UUID): Product ID.

        Returns:
            int: Total number of reviews.
        """
        stmt = select(func.count()).select_from(Review).where(Review.product_id == product_id)
        result = await self._session.exec(stmt)
        return result.first() or 0

    async def average_rating(self, product_id: UUID) -> float | None:
        """Get the average rating for a product.

        Args:
            product_id (UUID): Product ID.

        Returns:
            float | None: Average rating or none if no reviews.
        """
        stmt = select(func.avg(Review.rating)).where(Review.product_id == product_id)
        result = await self._session.exec(stmt)
        avg_rating = result.first()
        return float(avg_rating) if avg_rating is not None else None
