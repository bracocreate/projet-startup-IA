from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models import Source, SourceStatus
from app.schemas.system import DashboardSummaryRead, RankingSection, SourceRead

router = APIRouter(tags=["Tableau de bord"])


def to_source_read(s: Source) -> SourceRead:
    return SourceRead(
        id=str(s.id),
        slug=s.slug,
        name=s.name,
        family=s.family,
        country=s.country,
        access_method=s.access_method.value,
        status=s.status.value,
        is_demo=s.is_demo,
    )


@router.get("/dashboard/summary", response_model=DashboardSummaryRead)
def dashboard_summary(
    db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
) -> DashboardSummaryRead:
    rows = db.execute(select(Source.status, func.count()).group_by(Source.status)).all()
    by_status = {status.value: int(count) for status, count in rows}
    total = sum(by_status.values())
    errors = db.scalars(
        select(Source).where(Source.status.in_([SourceStatus.error, SourceStatus.degraded]))
    ).all()
    demo_count = db.scalar(select(func.count()).where(Source.is_demo.is_(True))) or 0

    # Phase 1 : aucune collecte n'existe encore → pas de date d'actualisation.
    last_refresh_at: datetime | None = None
    is_stale = last_refresh_at is None

    rankings = [
        RankingSection(
            key="best_deals",
            title="Meilleures affaires immédiates",
            status="not_implemented",
            message="Aucune offre : aucun connecteur n'est encore actif (Phase 3–4).",
            items=[],
        ),
        RankingSection(
            key="emerging_trends",
            title="Tendances et opportunités émergentes",
            status="not_implemented",
            message="Aucune source de tendances autorisée n'est encore intégrée (Phase 6).",
            items=[],
        ),
        RankingSection(
            key="new_markets",
            title="Nouveaux marchés à explorer",
            status="not_implemented",
            message="Le moteur de découverte n'est pas encore disponible (Phase 7).",
            items=[],
        ),
    ]
    return DashboardSummaryRead(
        generated_at=datetime.now(UTC),
        data_mode="demo" if demo_count else "empty",
        last_refresh_at=last_refresh_at,
        is_stale=is_stale,
        stale_after_hours=settings.stale_after_hours,
        sources_total=total,
        sources_by_status=by_status,
        sources_in_error=[to_source_read(s) for s in errors],
        pending_discoveries=0,
        rankings=rankings,
    )
