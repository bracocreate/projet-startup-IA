from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_actor
from app.connectors.base import SearchQuery
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.catalog import (
    CollectRequest,
    ConnectorInfoRead,
    ConnectorRunRead,
    SourceTestRead,
)
from app.schemas.system import SourceRead
from app.services.collection_service import CollectionRefusedError
from app.services.connector_service import collect_from_source, list_connectors, test_source
from app.services.offer_service import list_runs, to_run_read
from app.services.source_service import list_sources

router = APIRouter(tags=["Sources"])


@router.get("/sources", response_model=list[SourceRead])
def read_sources(db: Session = Depends(get_db)) -> list[SourceRead]:
    return list_sources(db)


@router.get(
    "/connectors",
    response_model=list[ConnectorInfoRead],
    summary="Connecteurs implémentés, configuration et quotas du jour",
)
def read_connectors(
    db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
) -> list[ConnectorInfoRead]:
    return list_connectors(db, settings)


@router.post(
    "/sources/{slug}/test",
    response_model=SourceTestRead,
    summary="Test réel de connexion (seul un succès rend la source active)",
)
def post_test_source(
    slug: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: str = Depends(require_actor),
) -> SourceTestRead:
    try:
        return test_source(db, slug, actor, settings)
    except CollectionRefusedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post(
    "/sources/{slug}/collect",
    response_model=ConnectorRunRead,
    summary="Lance une collecte (appelable par n8n ou un planificateur)",
)
def post_collect(
    slug: str,
    body: CollectRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: str = Depends(require_actor),
) -> ConnectorRunRead:
    query = SearchQuery(
        keywords=body.keywords.strip(),
        brand=body.brand.strip() if body.brand else None,
        gtin=body.gtin,
        max_price=body.max_price,
        limit=body.limit,
    )
    try:
        return to_run_read(collect_from_source(db, slug, query, actor, settings))
    except CollectionRefusedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.get(
    "/connector-runs",
    response_model=list[ConnectorRunRead],
    summary="Dernières exécutions de connecteurs",
)
def read_connector_runs(
    db: Session = Depends(get_db), limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> list[ConnectorRunRead]:
    return list_runs(db, limit)
