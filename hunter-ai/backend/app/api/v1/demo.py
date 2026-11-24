from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_actor
from app.db.session import get_db
from app.schemas.catalog import ConnectorRunRead, DemoPurgeRead
from app.services.collection_service import CollectionRefusedError
from app.services.demo_service import load_demo, purge_demo
from app.services.offer_service import to_run_read

router = APIRouter(prefix="/demo", tags=["Données DEMO"])


@router.post(
    "/load",
    response_model=ConnectorRunRead,
    summary="Charge (ou recharge) les données de démonstration fictives",
)
def post_load_demo(
    db: Session = Depends(get_db), actor: str = Depends(require_actor)
) -> ConnectorRunRead:
    try:
        return to_run_read(load_demo(db, actor))
    except CollectionRefusedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.delete("", response_model=DemoPurgeRead, summary="Supprime toutes les données DEMO")
def delete_demo(
    db: Session = Depends(get_db), actor: str = Depends(require_actor)
) -> DemoPurgeRead:
    return purge_demo(db, actor)
