from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.system import HealthRead, SystemStatusRead
from app.services.system_service import build_health, build_system_status

router = APIRouter(tags=["Système"])


@router.get("/health", response_model=HealthRead, summary="Contrôle de santé")
def health(response: Response, db: Session = Depends(get_db)) -> HealthRead:
    result = build_health(db)
    if result.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result


@router.get("/system/status", response_model=SystemStatusRead, summary="Santé du système")
def system_status(
    db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
) -> SystemStatusRead:
    return build_system_status(db, settings)
