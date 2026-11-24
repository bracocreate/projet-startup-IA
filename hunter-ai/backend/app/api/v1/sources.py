from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.catalog import ConnectorRunRead
from app.schemas.system import SourceRead
from app.services.offer_service import list_runs
from app.services.source_service import list_sources

router = APIRouter(tags=["Sources"])


@router.get("/sources", response_model=list[SourceRead])
def read_sources(db: Session = Depends(get_db)) -> list[SourceRead]:
    return list_sources(db)


@router.get(
    "/connector-runs",
    response_model=list[ConnectorRunRead],
    summary="Dernières exécutions de connecteurs",
)
def read_connector_runs(
    db: Session = Depends(get_db), limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> list[ConnectorRunRead]:
    return list_runs(db, limit)
