"""Utility functions for generating unique slugs."""

from slugify import slugify
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.category import Category
from app.models.product import Product

SlugContext = type["Category"] | type["Product"]


async def generate_slug(
    session: AsyncSession,
    name: str,
    model: SlugContext,
) -> str:
    """Generate a unique slug for a given name and model.

    Args:
        session (AsyncSession): The database session.
        name (str): The name to generate the slug from.
        model (SlugContext): The model class (Category or Product).

    Returns:
        str: A unique slug.
    """
    base_slug = slugify(name)
    slug = base_slug
    counter = 1

    while True:
        stmt = select(model).where(model.slug == slug)
        existing = (await session.exec(stmt)).first()

        if not existing:
            return slug

        slug = f"{base_slug}-{counter}"
        counter += 1
