"""Health check route."""

from fastapi import APIRouter

from app.api.v1.dependencies import SessionDep
from app.db.database import check_db_health

router = APIRouter(prefix="/api/v1/", tags=["Meta"])


@router.get("/health", summary="Database Health Check")
async def health_check(session: SessionDep) -> dict[str, str]:
    """Health check endpoint to verify that the API is running."""
    if not await check_db_health(session):
        return {"status": "unhealthy"}
    return {"status": "healthy"}
