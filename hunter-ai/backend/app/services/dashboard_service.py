"""Construction du résumé du tableau de bord (dernier état connu)."""

from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import Source, SourceStatus
from app.schemas.system import DashboardSummaryRead, RankingSection
from app.services.source_service import to_source_read

# Phase 1 : aucun moteur de classement n'existe encore. Chaque section l'indique explicitement.
RankingKey = Literal["best_deals", "emerging_trends", "new_markets"]

PLACEHOLDER_RANKINGS: tuple[tuple[RankingKey, str, str], ...] = (
    (
        "best_deals",
        "Meilleures affaires immédiates",
        "Aucune offre : aucun connecteur n'est encore actif (Phase 3–4).",
    ),
    (
        "emerging_trends",
        "Tendances et opportunités émergentes",
        "Aucune source de tendances autorisée n'est encore intégrée (Phase 6).",
    ),
    (
        "new_markets",
        "Nouveaux marchés à explorer",
        "Le moteur de découverte n'est pas encore disponible (Phase 7).",
    ),
)


def build_dashboard_summary(db: Session, settings: Settings) -> DashboardSummaryRead:
    rows = db.execute(select(Source.status, func.count()).group_by(Source.status)).all()
    by_status = {status.value: int(count) for status, count in rows}
    errors = db.scalars(
        select(Source).where(Source.status.in_([SourceStatus.error, SourceStatus.degraded]))
    ).all()
    demo_count = db.scalar(select(func.count()).where(Source.is_demo.is_(True))) or 0

    # Phase 1 : aucune collecte n'existe encore → pas de date d'actualisation.
    last_refresh_at: datetime | None = None

    return DashboardSummaryRead(
        generated_at=datetime.now(UTC),
        data_mode="demo" if demo_count else "empty",
        last_refresh_at=last_refresh_at,
        is_stale=last_refresh_at is None,
        stale_after_hours=settings.stale_after_hours,
        sources_total=sum(by_status.values()),
        sources_by_status=by_status,
        sources_in_error=[to_source_read(s) for s in errors],
        pending_discoveries=0,
        rankings=[
            RankingSection(key=key, title=title, status="not_implemented", message=msg, items=[])
            for key, title, msg in PLACEHOLDER_RANKINGS
        ],
    )
