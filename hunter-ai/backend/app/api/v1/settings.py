from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_actor
from app.api.v1.dashboard import to_source_read
from app.db.session import get_db
from app.models import Source
from app.schemas.settings import SettingsRead, SettingsUpdate
from app.schemas.system import SourceRead
from app.services.settings_service import get_or_create_settings, update_settings

router = APIRouter()


@router.get("/settings", response_model=SettingsRead, tags=["Paramètres"])
def read_settings(db: Session = Depends(get_db)) -> SettingsRead:
    return SettingsRead.model_validate(get_or_create_settings(db))


@router.patch("/settings", response_model=SettingsRead, tags=["Paramètres"])
def patch_settings(
    patch: SettingsUpdate,
    db: Session = Depends(get_db),
    actor: str = Depends(require_actor),
) -> SettingsRead:
    return SettingsRead.model_validate(update_settings(db, patch, actor))


@router.get("/sources", response_model=list[SourceRead], tags=["Sources"])
def list_sources(db: Session = Depends(get_db)) -> list[SourceRead]:
    return [to_source_read(s) for s in db.scalars(select(Source).order_by(Source.name)).all()]
