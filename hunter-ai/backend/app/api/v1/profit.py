import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_actor
from app.db.session import get_db
from app.engines.profit_engine.calculator import ProfitInputs, calculate
from app.schemas.profit import (
    ProfitRequest,
    ProfitResultRead,
    ResaleRecordCreate,
    ResaleRecordPage,
    ResaleRecordRead,
    ResaleReferenceRead,
)
from app.services import resale_service
from app.services.offer_service import NotFoundError

router = APIRouter()


@router.post(
    "/profit/calculate",
    response_model=ProfitResultRead,
    tags=["Rentabilité"],
    summary="Coût rendu et rentabilité (calcul déterministe, rien n'est enregistré)",
)
def post_calculate(body: ProfitRequest) -> ProfitResultRead:
    result = calculate(ProfitInputs(**body.model_dump()))
    return ProfitResultRead.model_validate(result, from_attributes=True)


@router.get("/resale-records", response_model=ResaleRecordPage, tags=["Ventes réalisées"])
def read_records(
    db: Session = Depends(get_db),
    brand: Annotated[str | None, Query(max_length=120)] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ResaleRecordPage:
    return resale_service.list_records(db, brand, q, limit, offset)


@router.get(
    "/resale-records/reference",
    response_model=ResaleReferenceRead,
    tags=["Ventes réalisées"],
    summary="Prix de revente de référence calculé sur vos ventes réalisées",
)
def read_reference(
    db: Session = Depends(get_db),
    brand: Annotated[str | None, Query(max_length=120)] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
) -> ResaleReferenceRead:
    return resale_service.reference(db, brand, q)


@router.post(
    "/resale-records",
    response_model=ResaleRecordRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Ventes réalisées"],
)
def post_record(
    body: ResaleRecordCreate, db: Session = Depends(get_db), actor: str = Depends(require_actor)
) -> ResaleRecordRead:
    return resale_service.create_record(db, body, actor)


@router.delete(
    "/resale-records/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Ventes réalisées"],
)
def delete_record(
    record_id: uuid.UUID, db: Session = Depends(get_db), actor: str = Depends(require_actor)
) -> Response:
    try:
        resale_service.delete_record(db, record_id, actor)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
