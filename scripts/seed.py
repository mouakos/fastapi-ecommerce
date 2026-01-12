"""Seed data for development and testing."""

import asyncio

from sqlmodel import select

from app.db.database import AsyncSessionLocal, async_engine
from app.models.category import Category
from app.models.product import Product

categories = [
    {
        "name": "Electronics",
        "slug": "electronics",
        "description": "Electronic gadgets and devices.",
    },
    {
        "name": "Books",
        "slug": "books",
        "description": "A variety of books across different genres.",
    },
    {
        "name": "Clothing",
        "slug": "clothing",
        "description": "Apparel for men, women, and children.",
    },
    {
        "name": "Home & Kitchen",
        "slug": "home-kitchen",
        "description": "Essentials for home and kitchen.",
    },
    {
        "name": "Sports & Outdoors",
        "slug": "sports-outdoors",
        "description": "Gear and equipment for outdoor activities.",
    },
]

products = [
    {
        "name": "Wireless Headphones",
        "slug": "wireless-headphones",
        "description": "High-quality wireless headphones with noise cancellation.",
        "price": 99.99,
        "stock": 50,
        "sku": "WH-001",
        "image_url": "https://example.com/images/wireless-headphones.jpg",
        "is_published": True,
    },
    {
        "name": "Science Fiction Novel",
        "slug": "science-fiction-novel",
        "description": "A thrilling science fiction novel set in a dystopian future.",
        "price": 14.99,
        "stock": 200,
        "sku": "BK-001",
        "image_url": "https://example.com/images/science-fiction-novel.jpg",
        "is_published": True,
    },
    {
        "name": "Men's T-Shirt",
        "slug": "mens-tshirt",
        "description": "Comfortable cotton t-shirt for men.",
        "price": 19.99,
        "stock": 100,
        "sku": "CL-001",
        "image_url": "https://example.com/images/mens-tshirt.jpg",
        "is_published": True,
    },
    {
        "name": "Blender",
        "slug": "blender",
        "description": "High-speed blender for smoothies and soups.",
        "price": 49.99,
        "stock": 30,
        "sku": "HK-001",
        "image_url": "https://example.com/images/blender.jpg",
        "is_published": True,
    },
    {
        "name": "Yoga Mat",
        "slug": "yoga-mat",
        "description": "Non-slip yoga mat for all types of exercises.",
        "price": 29.99,
        "stock": 75,
        "sku": "SO-001",
        "image_url": "https://example.com/images/yoga-mat.jpg",
        "is_published": True,
    },
    {
        "name": "Smartphone",
        "slug": "smartphone",
        "description": "Latest model smartphone with advanced features.",
        "price": 699.99,
        "stock": 40,
        "sku": "WH-002",
        "image_url": "https://example.com/images/smartphone.jpg",
        "is_published": True,
    },
]


async def seed_data() -> None:
    """Seed database with sample categories and products."""
    async with AsyncSessionLocal() as session:
        print("Starting database seeding...")

        # Clear existing data
        print("Clearing existing products...")
        product_result = await session.exec(select(Product))
        for product in product_result.all():
            await session.delete(product)

        print("Clearing existing categories...")
        category_result = await session.exec(select(Category))
        for category in category_result.all():
            await session.delete(category)

        await session.commit()

        # Seed categories
        print(f"Creating {len(categories)} categories...")
        for cat_data in categories:
            category = Category(**cat_data)
            session.add(category)
        await session.commit()

        # Seed products
        print(f"Creating {len(products)} products...")
        for prod_data in products:
            product = Product(**prod_data)
            session.add(product)

        await session.commit()
        print("✓ Database seeded successfully!")


async def main() -> None:
    """Main entry point that properly closes the engine."""
    await seed_data()
    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
