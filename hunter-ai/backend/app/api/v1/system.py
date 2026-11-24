import logging
from datetime import UTC, datetime
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import APP_VERSION, Settings, get_settings
from app.db.session import get_db
from app.schemas.system import ComponentStatus, HealthRead, SystemStatusRead

router = APIRouter(tags=["Système"])
logger = logging.getLogger("hunter.system")

BACKEND_ROOT = Path(__file__).resolve().parents[3]


def _expected_revision() -> str | None:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    return ScriptDirectory.from_config(cfg).get_current_head()


def _db_ok(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        logger.exception("Base de données injoignable")
        return False


@router.get("/health", response_model=HealthRead, summary="Contrôle de santé")
def health(response: Response, db: Session = Depends(get_db)) -> HealthRead:
    ok = _db_ok(db)
    if not ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthRead(
        status="ok" if ok else "degraded",
        database="ok" if ok else "error",
        version=APP_VERSION,
        time_utc=datetime.now(UTC),
    )


@router.get("/system/status", response_model=SystemStatusRead, summary="Santé du système")
def system_status(
    db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
) -> SystemStatusRead:
    components: list[ComponentStatus] = []
    revision: str | None = None
    expected = _expected_revision()

    if _db_ok(db):
        components.append(
            ComponentStatus(name="Base de données", status="ok", detail="PostgreSQL joignable")
        )
        try:
            revision = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
        except SQLAlchemyError:
            db.rollback()
        if revision == expected:
            components.append(
                ComponentStatus(name="Migrations", status="ok", detail=f"À jour ({revision})")
            )
        else:
            components.append(
                ComponentStatus(
                    name="Migrations",
                    status="warning",
                    detail=f"Révision {revision or 'aucune'} ≠ attendue {expected}. "
                    "Lancez `make migrate`.",
                )
            )
    else:
        components.append(
            ComponentStatus(name="Base de données", status="error", detail="PostgreSQL injoignable")
        )

    components += [
        ComponentStatus(
            name="Connecteurs de données",
            status="not_implemented",
            detail="Aucun connecteur actif (prévu en Phase 3).",
        ),
        ComponentStatus(
            name="Planificateur",
            status="not_implemented",
            detail="Collecte quotidienne non encore planifiée (prévu en Phase 8).",
        ),
        ComponentStatus(
            name="Telegram",
            status="not_configured",
            detail="Notifications optionnelles, non configurées (Phase 8).",
        ),
    ]
    return SystemStatusRead(
        version=APP_VERSION,
        environment=settings.app_env,
        timezone=settings.app_timezone,
        time_utc=datetime.now(UTC),
        db_revision=revision,
        db_revision_expected=expected,
        components=components,
    )
