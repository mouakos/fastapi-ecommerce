"""SQL Product repository implementation."""

from datetime import timedelta
from uuid import UUID

from slugify import slugify
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.product_repository import ProductRepository, allowed_sort_by, allowed_sort_order
from app.models.category import Category
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.review import Review
from app.repositories.sql_generic_repository import SqlGenericRepository
from app.utils.utc_time import utcnow


class SqlProductRepository(SqlGenericRepository[Product], ProductRepository):
    """SQL Product repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        super().__init__(session, Product)

    async def paginate(
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
        sort_by: allowed_sort_by = "id",
        sort_order: allowed_sort_order = "asc",
    ) -> tuple[list[Product], int]:
        """Gets a list of products with optional filters, sorting, and pagination.

        Args:
            page (int, optional): Page number for pagination.
            per_page (int, optional): Number of items per page for pagination.
            search (str | None): Search query to filter products by name or description.
            category_id (UUID | None): Category ID to filter products.
            category_slug (str | None): Category slug to filter products.
            min_price (float | None): Minimum price to filter products.
            max_price (float | None): Maximum price to filter products.
            min_rating (float | None): Minimum average rating to filter products.
            availability (str | None): Stock availability filter ("in_stock", "out_of_stock", "all").
            sort_by (allowed_sort_by, optional): Field to sort by (e.g., "price", "name", "rating").
            sort_order (allowed_sort_order, optional): Sort order ("asc" or "desc").

        Returns:
            tuple[list[Product], int]: A tuple containing a list of products and the total number of items.
        """
        page = max(page, 1)
        per_page = max(min(per_page, 100), 1)

        # Base query
        stmt = select(Product).where(Product.is_active)

        # Apply filters
        if search:
            search_term = f"%{search.lower()}%"
            stmt = stmt.where(
                (func.lower(Product.name).like(search_term))
                | (func.lower(Product.description).like(search_term))
            )
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)

        if category_slug is not None:
            stmt = stmt.join(Product.category).where(Category.slug == category_slug)  # type: ignore [arg-type]

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
                select(func.count())
                .select_from(Review)
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
        total = (await self._session.exec(count_stmt)).first() or 0

        # Apply pagination
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        result = await self._session.exec(stmt)
        products = list(result.all())

        return products, total

    async def find_by_slug(self, slug: str) -> Product | None:
        """Find a single product by slug.

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

    async def count_reviews(self, product_id: UUID) -> int:
        """Count the total number of reviews for a product.

        Args:
            product_id (UUID): Product ID.

        Returns:
            int: Total number of reviews.
        """
        stmt = select(func.count()).select_from(Review).where(Review.product_id == product_id)
        result = await self._session.exec(stmt)
        return result.first() or 0

    async def calculate_average_rating(self, product_id: UUID) -> float | None:
        """Calculate the average rating for a product.

        Args:
            product_id (UUID): Product ID.

        Returns:
            float | None: Average rating or none if no reviews.
        """
        stmt = select(func.avg(Review.rating)).where(Review.product_id == product_id)
        result = await self._session.exec(stmt)
        avg_rating = result.first()
        return float(avg_rating) if avg_rating is not None else None

    async def list_autocomplete_suggestions(self, query: str, limit: int = 10) -> list[str]:
        """Get autocomplete suggestions for product names based on a search query.

        Args:
            query (str): Search query.
            limit (int, optional): Maximum number of suggestions to return. Defaults to 5.

        Returns:
            list[str]: List of suggested product names.
        """
        if not query or len(query) < 2:
            return []

        # Priority 1: Prefix matches (starts with query)
        prefix_pattern = f"{query}%"
        stmt = (
            select(Product.name)
            .where(Product.name.ilike(prefix_pattern))  # type: ignore[attr-defined]
            .where(Product.is_active)
            .distinct()
            .limit(limit)
        )
        result = await self._session.exec(stmt)
        prefix_matches = list(result.all())

        if len(prefix_matches) >= limit:
            return prefix_matches

        # Priority 2: Contains matches (query appears anywhere)
        contains_pattern = f"%{query}%"
        remaining = limit - len(prefix_matches)
        stmt = (
            select(Product.name)
            .where(Product.name.ilike(contains_pattern))  # type: ignore[attr-defined]
            .where(~Product.name.ilike(prefix_pattern))  # type: ignore[attr-defined]
            .where(Product.is_active)
            .distinct()
            .limit(remaining)
        )

        result = await self._session.exec(stmt)
        contains_matches = list(result.all())

        return prefix_matches + contains_matches

    async def count_low_stock(self, threshold: int = 10) -> int:
        """Get number of products that are low in stock.

        Args:
            threshold (int): Stock threshold.

        Returns:
            int: Number of products that are low in stock.
        """
        stmt = (
            select(func.count())
            .select_from(Product)
            .where(Product.stock <= threshold)
            .where(Product.is_active)
        )
        result = await self._session.exec(stmt)
        return result.first() or 0

    async def list_low_stock(
        self, threshold: int = 10, page: int = 1, page_size: int = 10
    ) -> tuple[list[Product], int]:
        """Retrieve products that are low in stock.

        Args:
            threshold (int): Stock threshold.
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of products per page. Defaults to 10.

        Returns:
            tuple[list[Product], int]: List of low stock products and total count.
        """
        stmt = (
            select(Product)
            .where(Product.stock <= threshold)
            .where(Product.is_active)
            .order_by(Product.stock.asc())  # type: ignore [attr-defined]
        )

        # total items matching filters
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.exec(count_stmt)).first() or 0

        # Apply pagination
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self._session.exec(stmt)
        return list(result.all()), total

    async def list_top_selling(self, limit: int = 10, days: int = 30) -> list[Product]:
        """Retrieve top selling products within a specified time frame.

        Args:
            limit (int): Number of top selling products to retrieve.
            days (int): Number of days to consider for sales data.

        Returns:
            list[Product]: List of top selling products.
        """
        cutoff_date = utcnow() - timedelta(days=days)

        stmt = (
            select(
                Product,
                func.sum(OrderItem.quantity).label("total_sold"),
            )
            .join(OrderItem, OrderItem.product_id == Product.id)  # type: ignore [arg-type]
            .join(
                Order,
                OrderItem.order_id == Order.id,  # type: ignore [arg-type]
            )
            .where(Order.status == OrderStatus.PAID)
            .where(Order.created_at >= cutoff_date)
            .group_by(Product.id)  # type: ignore [arg-type]
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(limit)
        )

        result = await self._session.exec(stmt)
        top_selling = result.all()
        return [item[0] for item in top_selling]
