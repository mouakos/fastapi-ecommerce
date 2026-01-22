"""Middleware for handling exceptions."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import AppError
from app.core.logger import logger


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers with the FastAPI application."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Handle all custom application errors."""
        logger.warning(
            f"{exc.error_code}",
            status_code=exc.status_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "error_code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle FastAPI/Pydantic request validation errors."""
        errors = exc.errors()
        logger.warning(
            "request_validation_error",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            message="Request validation failed.",
            details={"errors": errors},
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "error_code": "request_validation_error",
                    "message": "Request validation failed.",
                    "details": {"errors": errors},
                }
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """Handle SQLAlchemy exceptions globally."""
        logger.error(
            "database_error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="A database error occurred.",
            details={"exception": str(exc)},
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "error_code": "database_error",
                    "message": "A database error occurred.",
                    "details": None,
                }
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unhandled exceptions globally."""
        logger.error(
            "internal_server_error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred.",
            details={"exception": str(exc)},
            path=request.url.path,
            method=request.method,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "error_code": "internal_server_error",
                    "message": "An unexpected error occurred.",
                    "details": None,
                }
            },
        )
