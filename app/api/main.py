"""Main application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from app.api.cache import init_in_memory_caching, init_redis_caching  # noqa: F401
from app.api.exception_handlers import register_exception_handlers
from app.api.middleware import register_middleware
from app.api.rate_limit import init_redis_rate_limiter
from app.api.v1.routers import router
from app.core.config import settings
from app.core.logger import logger
from app.db.database import async_engine, init_db
from app.db.redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:  # noqa: ARG001
    """Lifespan context manager for startup and shutdown events."""
    logger.info("application_starting", environment=settings.environment)
    await init_db()

    await redis_client.connect()
    if settings.cache_enabled:
        init_redis_caching()
        logger.info("cache_initialized", cache_type="redis")

        # Uncomment for in-memory caching instead of Redis
        # init_in_memory_caching()
        # logger.info("in_memory_cache_initialized")

    if settings.rate_limiting_enabled:
        await init_redis_rate_limiter()

    logger.info("application_ready", version=settings.app_version)
    yield
    logger.info("application_shutting_down")
    await redis_client.close()
    await async_engine.dispose()
    logger.info("application_stopped")


app = FastAPI(
    lifespan=lifespan,
    description="This is a simple RESTful  API to for managing the products catalog, user authentication, shopping cart, and order processing in an e-commerce platform.",
    version=settings.app_version,
    root_path="/api/v1",
    servers=[],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    title="E-commerce API",
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/license/mit/",
    },
    contact={
        "name": "Stephane Mouako",
        "url": "https://github.com/mouakos",
    },
    swagger_ui_parameters={
        "syntaxHighlight.theme": "monokai",
        "layout": "BaseLayout",
        "filter": True,
        "tryItOutEnabled": True,
        "onComplete": "Ok",
    },
    openapi_tags=[
        {
            "name": "Root",
            "description": "API root endpoint with welcome message and documentation links.",
        },
        {
            "name": "Health Check",
            "description": "Database connectivity monitoring for health checks and readiness probes.",
        },
        {
            "name": "Authentication",
            "description": "User registration and login with JWT token authentication and cart merging.",
        },
        {
            "name": "Users",
            "description": "User profile management including personal information updates.",
        },
        {
            "name": "Addresses",
            "description": "Delivery and billing address management for authenticated users.",
        },
        {
            "name": "Categories",
            "description": "Product category management with hierarchical organization and CRUD operations.",
        },
        {
            "name": "Products",
            "description": "Product catalog with advanced filtering, search, autocomplete, and admin CRUD operations.",
        },
        {
            "name": "Reviews",
            "description": "Customer product reviews with rating, comments, and moderation support.",
        },
        {
            "name": "Wishlist",
            "description": "Save and organize favorite products with options to move items to cart.",
        },
        {
            "name": "Cart",
            "description": "Shopping cart management for authenticated users and guest sessions.",
        },
        {
            "name": "Orders",
            "description": "Order checkout, processing, and history management.",
        },
        {
            "name": "Payments",
            "description": "Stripe payment integration with checkout sessions and webhook processing.",
        },
        {
            "name": "Admin",
            "description": "Administrative dashboard with analytics, user management, order processing, review moderation, and inventory tracking.",
        },
    ],
)


register_exception_handlers(app)
register_middleware(app)


class RootRead(BaseModel):
    """Schema for root response."""

    message: str


@app.get("/", tags=["Root"], response_model=RootRead)
def read_root() -> RootRead:
    """Returns a welcome message for the API root."""
    return RootRead(message="Welcome to the E-Commerce API v1. Check out /docs for the spec!")


app.include_router(router)
