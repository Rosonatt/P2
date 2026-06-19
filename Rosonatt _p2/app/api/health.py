"""Healthcheck da aplicação."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.dependencies.database import get_db
from app.schemas.common import HealthData, SuccessResponse

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get(
    "/health",
    response_model=SuccessResponse[HealthData],
    summary="Verifica saúde da API e conexão com o banco",
)
def health_check(db: Session = Depends(get_db)) -> SuccessResponse[HealthData]:
    """Endpoint usado por orquestradores e monitoramento."""
    try:
        db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception:
        database_status = "disconnected"

    return SuccessResponse(
        data=HealthData(
            status="healthy" if database_status == "connected" else "degraded",
            app_name=settings.app_name,
            version=settings.app_version,
            environment=settings.environment,
            database=database_status,
        )
    )
