"""Main application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from app.api.v1.routers import router
from app.db.database import async_engine, init_db


class RootRead(BaseModel):
    """Schema for root response."""

    message: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:  # noqa: ARG001
    """Lifespan context manager for startup and shutdown events."""
    # Startup actions
    await init_db()
    yield
    # Shutdown actions
    await async_engine.dispose()


app = FastAPI(
    lifespan=lifespan,
    description="This is a simple RESTful  API to for managing the products catalog, user authentication, shopping cart, and order processing in an e-commerce platform.",
    version="1.0.0",
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
            "description": "API Root endpoint.",
        },
        {
            "name": "Healthcheck",
            "description": "Endpoints to check the health status of the database connection.",
        },
        {
            "name": "Authentication",
            "description": "Operations related to user authentication and registration.",
        },
        {
            "name": "Users",
            "description": "Operations related to user management.",
        },
        {
            "name": "Addresses",
            "description": "Operations related to user delivery and billing addresses.",
        },
        {
            "name": "Categories",
            "description": "Operations related to category management.",
        },
        {
            "name": "Products",
            "description": "Operations related to product management.",
        },
        {
            "name": "Reviews",
            "description": "Operations related to product reviews.",
        },
        {
            "name": "Wishlist",
            "description": "Operations related to wishlist management.",
        },
        {
            "name": "Cart",
            "description": "Operations related to shopping cart management.",
        },
        {
            "name": "Orders",
            "description": "Operations related to order processing and management.",
        },
        {
            "name": "Payments",
            "description": "Operations related to payment processing.",
        },
        {
            "name": "Admin",
            "description": "Administrative operations and analytics.",
        },
    ],
)


@app.get("/", tags=["Root"], response_model=RootRead)
def read_root() -> RootRead:
    """Returns a welcome message for the API root."""
    return RootRead(message="Welcome to the E-Commerce API v1. Check out /docs for the spec!")


app.include_router(router)
