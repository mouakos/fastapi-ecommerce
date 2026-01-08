"""Health check route."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import check_db_health, get_session

router = APIRouter(prefix="/api/v1/health", tags=["HealthCheck"])


@router.get("/", summary="Database Health Check")
async def health_check(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, str]:
    """Health check endpoint to verify that the API is running."""
    if not await check_db_health(session):
        return {"status": "unhealthy"}
    return {"status": "healthy"}
