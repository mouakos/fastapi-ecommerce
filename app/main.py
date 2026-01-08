"""Main application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:  # noqa: ARG001
    """Lifespan context manager for startup and shutdown events."""
    # Startup actions can be added here
    # await init_db()
    yield
    # Shutdown actions can be added here


app = FastAPI(
    lifespan=lifespan,
    description="This is a simple RESTful  API to for managing the products catalog, user authentication, shopping cart, and order processing in an e-commerce platform.",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    title="E-commerce API",
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/license/mit/",
    },
    version="v1",
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
            "name": "HealthCheck",
            "description": "Endpoints for checking the health status of the Database.",
        },
        {
            "name": "Products",
            "description": "Operations related to product management.",
        },
        {
            "name": "Categories",
            "description": "Operations related to category management.",
        },
    ],
)


app.include_router(router)
