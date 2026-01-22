"""Error response schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorDetail(BaseModel):
    """Detailed error information."""

    message: str
    error_code: str
    details: dict[str, Any] = {}


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: ErrorDetail

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "message": "User not found.",
                    "error_code": "RESOURCE_NOT_FOUND",
                    "details": {"resource": "User", "user_id": "123e4567..."},
                }
            }
        }
    )
