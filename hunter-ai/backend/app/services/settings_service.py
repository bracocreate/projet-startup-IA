from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, UserSettings
from app.models.user import DEFAULT_MARKETS, DEFAULT_PRIORITY_BRANDS
from app.schemas.settings import SettingsUpdate
from app.services.audit import record_audit

LOCAL_USERNAME = "local"


def get_local_user(db: Session) -> User:
    """Utilisateur unique (usage personnel). Créé à la première demande."""
    user = db.scalar(select(User).where(User.username == LOCAL_USERNAME))
    if user is None:
        user = User(username=LOCAL_USERNAME, display_name="Utilisateur principal")
        db.add(user)
        db.flush()
    return user


def get_or_create_settings(db: Session) -> UserSettings:
    user = get_local_user(db)
    settings = db.scalar(select(UserSettings).where(UserSettings.user_id == user.id))
    if settings is None:
        settings = UserSettings(
            user_id=user.id,
            markets=list(DEFAULT_MARKETS),
            priority_brands=list(DEFAULT_PRIORITY_BRANDS),
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_settings(db: Session, patch: SettingsUpdate, actor: str) -> UserSettings:
    settings = get_or_create_settings(db)
    changes: dict[str, Any] = {}
    for field, new in patch.model_dump(exclude_unset=True).items():
        old = getattr(settings, field)
        if old != new:
            changes[field] = {"old": _jsonable(old), "new": _jsonable(new)}
            setattr(settings, field, new)
    if changes:
        record_audit(
            db,
            actor=actor,
            action="settings.update",
            entity_type="user_settings",
            entity_id=settings.id,
            details={"changes": changes},
        )
        db.commit()
        db.refresh(settings)
    return settings


def _jsonable(v: Any) -> Any:
    if v is None or isinstance(v, bool | int | float | str):
        return v
    if isinstance(v, list):
        return [_jsonable(x) for x in v]
    return str(v)
