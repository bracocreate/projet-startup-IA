"""Actions sur les sources réelles : test de connexion, collecte à la demande, quotas.

Une source ne devient `active` qu'après un test réel réussi (règle du cahier des charges §4.2).
"""

from datetime import UTC, datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.connectors.base import ConnectorError, SearchQuery
from app.connectors.registry import (
    CONNECTORS,
    daily_call_budget,
    get_connector,
    is_configured,
)
from app.core.config import Settings
from app.models import AccessMethod, ConnectorRun, RunStatus, Source, SourceStatus
from app.schemas.catalog import ConnectorInfoRead, SourceTestRead
from app.services.audit import record_audit
from app.services.collection_service import (
    CollectionRefusedError,
    fetch_raw_offers,
    run_collection,
)

# Appels maximum d'une collecte (jeton + recherche) : réservés avant de lancer.
CALLS_PER_RUN = 2
TEST_QUERIES = {"aliexpress": SearchQuery(keywords="phone case", limit=3)}
DEFAULT_TEST_QUERY = SearchQuery(keywords="nike", limit=3)


def get_or_create_source(db: Session, slug: str, settings: Settings) -> Source:
    info = CONNECTORS.get(slug)
    if info is None:
        raise CollectionRefusedError(f"Aucun connecteur « {slug} » n'est implémenté.")
    source = db.scalar(select(Source).where(Source.slug == slug))
    if source is None:
        source = Source(
            slug=slug,
            name=info.name,
            family=info.family,
            homepage_url=info.homepage_url,
            access_method=AccessMethod.official_api,
            status=SourceStatus.needs_approval
            if is_configured(slug, settings)
            else SourceStatus.needs_credentials,
            terms_notes=info.description,
        )
        db.add(source)
        db.flush()
    return source


def calls_used_today(db: Session, source: Source) -> int:
    start = datetime.combine(datetime.now(UTC).date(), time.min, tzinfo=UTC)
    used = db.scalar(
        select(func.coalesce(func.sum(ConnectorRun.api_calls), 0)).where(
            ConnectorRun.source_id == source.id, ConnectorRun.started_at >= start
        )
    )
    return int(used or 0)


def check_budget(db: Session, source: Source, settings: Settings) -> None:
    budget = daily_call_budget(source.slug, settings)
    if budget is not None and calls_used_today(db, source) + CALLS_PER_RUN > budget:
        raise CollectionRefusedError(
            f"Quota journalier atteint pour « {source.name} » ({budget} appels). "
            "Reprise automatique demain (minuit UTC)."
        )


def list_connectors(db: Session, settings: Settings) -> list[ConnectorInfoRead]:
    sources = {s.slug: s for s in db.scalars(select(Source)).all()}
    result = []
    for info in CONNECTORS.values():
        source = sources.get(info.slug)
        budget = daily_call_budget(info.slug, settings)
        result.append(
            ConnectorInfoRead(
                slug=info.slug,
                name=info.name,
                description=info.description,
                configured=is_configured(info.slug, settings),
                status=source.status.value if source else None,
                daily_call_budget=budget,
                calls_used_today=calls_used_today(db, source) if source else 0,
            )
        )
    return result


def test_source(db: Session, slug: str, actor: str, settings: Settings) -> SourceTestRead:
    """Test réel : jeton + petite recherche. Seul un succès rend la source `active`."""
    source = get_or_create_source(db, slug, settings)
    connector = get_connector(slug, settings)
    if connector is None:  # pragma: no cover - garanti par get_or_create_source
        raise CollectionRefusedError(f"Aucun connecteur « {slug} ».")
    check_budget(db, source, settings)
    run = ConnectorRun(
        source_id=source.id, actor=actor, query={"test": "connexion"}, is_demo=source.is_demo
    )
    db.add(run)
    db.flush()
    try:
        test_query = TEST_QUERIES.get(slug, DEFAULT_TEST_QUERY)
        offers = fetch_raw_offers(connector, test_query)
    except Exception as exc:  # tout échec est consigné, jamais masqué
        detail = str(exc) if isinstance(exc, ConnectorError) else type(exc).__name__
        if not is_configured(slug, settings) or "identifiants" in detail.lower():
            source.status = SourceStatus.needs_credentials
        elif "refusé" in detail.lower():
            source.status = SourceStatus.needs_approval
        else:
            source.status = SourceStatus.error
        run.status = RunStatus.error
        run.errors = [detail]
        ok, count = False, 0
    else:
        count = len(offers)
        source.status = SourceStatus.active
        run.status = RunStatus.success
        run.offers_received = count
        detail = f"Test réel réussi : {count} annonce(s) reçue(s) pour « {test_query.keywords} »."
        source.terms_notes = (
            f"{CONNECTORS[slug].description}\nDernier test réussi : "
            f"{datetime.now(UTC):%Y-%m-%d %H:%M} UTC ({count} annonce(s))."
        )
        ok = True
    run.api_calls = int(getattr(connector, "api_calls", 0))
    run.finished_at = datetime.now(UTC)
    record_audit(
        db,
        actor=actor,
        action="source.test",
        entity_type="source",
        entity_id=source.id,
        details={"ok": ok, "status": source.status.value, "detail": detail[:300]},
    )
    db.commit()
    return SourceTestRead(
        ok=ok,
        status=source.status.value,
        detail=detail,
        sample_count=count,
        api_calls=run.api_calls,
    )


def collect_from_source(
    db: Session, slug: str, query: SearchQuery, actor: str, settings: Settings
) -> ConnectorRun:
    source = db.scalar(select(Source).where(Source.slug == slug))
    connector = get_connector(slug, settings)
    if source is None or connector is None:
        raise CollectionRefusedError(
            f"Source « {slug} » inconnue ou jamais testée : lancez d'abord le test de connexion."
        )
    check_budget(db, source, settings)
    return run_collection(db, source, connector, query, actor, settings.fx_rate_map)
