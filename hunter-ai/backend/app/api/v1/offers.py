import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models import Availability
from app.schemas.catalog import OfferDetailRead, OfferPage, PriceHistoryRead
from app.services.offer_service import (
    NotFoundError,
    OfferSort,
    get_offer,
    get_price_history,
    list_offers,
)

router = APIRouter(tags=["Offres"])


@router.get("/offers", response_model=OfferPage, summary="Offres collectées (filtres, pagination)")
def read_offers(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    q: Annotated[str | None, Query(max_length=200, description="Texte dans le titre")] = None,
    brand: Annotated[str | None, Query(max_length=120)] = None,
    source: Annotated[str | None, Query(max_length=80, description="Slug de la source")] = None,
    availability: Availability | None = None,
    is_demo: bool | None = None,
    max_price_eur: Annotated[Decimal | None, Query(ge=0)] = None,
    sort: OfferSort = "recent",
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> OfferPage:
    return list_offers(
        db,
        stale_after_hours=settings.stale_after_hours,
        limit=limit,
        offset=offset,
        sort=sort,
        q=q,
        brand=brand,
        source=source,
        availability=availability,
        is_demo=is_demo,
        max_price_eur=max_price_eur,
    )


@router.get("/offers/{offer_id}", response_model=OfferDetailRead, summary="Détail d'une offre")
def read_offer(
    offer_id: uuid.UUID,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OfferDetailRead:
    try:
        return get_offer(db, offer_id, settings.stale_after_hours)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get(
    "/products/{product_id}/price-history",
    response_model=PriceHistoryRead,
    tags=["Produits"],
    summary="Historique des prix observés pour un produit (toutes offres confondues)",
)
def read_price_history(product_id: uuid.UUID, db: Session = Depends(get_db)) -> PriceHistoryRead:
    try:
        return get_price_history(db, product_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
