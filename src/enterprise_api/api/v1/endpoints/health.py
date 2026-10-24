"""Health check and readiness probe endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_api.core.config import settings
from enterprise_api.core.database import get_db
from enterprise_api.schemas.common import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application Health & Readiness Probe",
    description="Validates API availability and active database connectivity.",
)
async def check_health(db: Annotated[AsyncSession, Depends(get_db)]) -> HealthResponse:
    db_ok = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        database_connected=db_ok,
        environment=settings.ENVIRONMENT,
    )
