"""Contrôles de santé : base de données, migrations, composants non encore livrés."""

import logging
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.connectors.registry import implemented_slugs
from app.core.config import APP_VERSION, Settings
from app.models import Source, SourceStatus
from app.schemas.system import ComponentStatus, HealthRead, SystemStatusRead

logger = logging.getLogger("hunter.system")

BACKEND_ROOT = Path(__file__).resolve().parents[2]

UPCOMING_COMPONENTS = (
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
)


@lru_cache
def expected_revision() -> str | None:
    """Révision Alembic attendue (tête des migrations livrées avec le code)."""
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    return ScriptDirectory.from_config(cfg).get_current_head()


def database_reachable(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        logger.exception("Base de données injoignable")
        return False


def current_revision(db: Session) -> str | None:
    try:
        return db.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except SQLAlchemyError:
        db.rollback()
        return None


def connectors_status(db: Session) -> ComponentStatus:
    sources = db.scalars(select(Source)).all()
    real_active = [s for s in sources if not s.is_demo and s.status == SourceStatus.active]
    failing = [s for s in sources if s.status in (SourceStatus.error, SourceStatus.degraded)]
    if failing:
        names = ", ".join(s.name for s in failing)
        return ComponentStatus(
            name="Connecteurs de données", status="error", detail=f"En erreur : {names}."
        )
    if real_active:
        return ComponentStatus(
            name="Connecteurs de données",
            status="ok",
            detail=f"{len(real_active)} source(s) réelle(s) active(s).",
        )
    demo = " Connecteur DEMO disponible." if "demo" in implemented_slugs() else ""
    return ComponentStatus(
        name="Connecteurs de données",
        status="not_configured",
        detail="Aucune source réelle active : configurez eBay (.env) puis lancez le test de "
        f"connexion dans « Sites et fournisseurs ».{demo}",
    )


def build_health(db: Session) -> HealthRead:
    ok = database_reachable(db)
    return HealthRead(
        status="ok" if ok else "degraded",
        database="ok" if ok else "error",
        version=APP_VERSION,
        time_utc=datetime.now(UTC),
    )


def build_system_status(db: Session, settings: Settings) -> SystemStatusRead:
    components: list[ComponentStatus] = []
    revision: str | None = None
    expected = expected_revision()

    if database_reachable(db):
        components.append(
            ComponentStatus(name="Base de données", status="ok", detail="PostgreSQL joignable")
        )
        revision = current_revision(db)
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

    if database_reachable(db):
        components.append(connectors_status(db))
    components.extend(UPCOMING_COMPONENTS)
    return SystemStatusRead(
        version=APP_VERSION,
        environment=settings.app_env,
        timezone=settings.app_timezone,
        time_utc=datetime.now(UTC),
        db_revision=revision,
        db_revision_expected=expected,
        components=components,
    )
