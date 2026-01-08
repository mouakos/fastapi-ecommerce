"""Utility functions for generating unique slugs."""

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


async def generate_slug(
    session: AsyncSession,
    name: str,
) -> str:
    """Generate a unique slug for a category based on its name."""
    base_slug = slugify(name)
    slug = base_slug
    counter = 1

    while True:
        stmt = select(Category).where(Category.slug == slug)  # type: ignore [arg-type]
        existing = (await session.execute(stmt)).scalars().first()

        if not existing:
            return slug

        slug = f"{base_slug}-{counter}"
        counter += 1
