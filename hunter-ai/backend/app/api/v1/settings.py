from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_actor
from app.db.session import get_db
from app.schemas.settings import SettingsRead, SettingsUpdate
from app.services.settings_service import get_or_create_settings, update_settings

router = APIRouter(tags=["Paramètres"])


@router.get("/settings", response_model=SettingsRead)
def read_settings(db: Session = Depends(get_db)) -> SettingsRead:
    return SettingsRead.model_validate(get_or_create_settings(db))


@router.patch("/settings", response_model=SettingsRead)
def patch_settings(
    patch: SettingsUpdate,
    db: Session = Depends(get_db),
    actor: str = Depends(require_actor),
) -> SettingsRead:
    return SettingsRead.model_validate(update_settings(db, patch, actor))
