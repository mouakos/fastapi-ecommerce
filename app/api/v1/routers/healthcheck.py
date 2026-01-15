"""Health check API route for monitoring database connectivity."""

from enum import StrEnum

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.v1.dependencies import SessionDep
from app.db.database import check_db_health

router = APIRouter(prefix="/healthcheck", tags=["Healthcheck"])


class DatabaseStatus(StrEnum):
    """Enum for database health status."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class HealthCheckRead(BaseModel):
    """Response model for health check."""

    status: DatabaseStatus
    message: str


@router.get(
    "",
    summary="Check database health",
    description="Verify database connectivity and return the current health status. Used for monitoring and readiness checks.",
    response_model=HealthCheckRead,
)
async def health_check(session: SessionDep) -> HealthCheckRead:
    """Health check endpoint to verify database connectivity."""
    if not await check_db_health(session):
        return HealthCheckRead(
            status=DatabaseStatus.UNHEALTHY, message="Database connection failed."
        )
    return HealthCheckRead(status=DatabaseStatus.HEALTHY, message="Database is connected.")
