"""Consultation des offres collectées, de leur historique et des exécutions de connecteurs."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal

from sqlalchemy import Select, UnaryExpression, func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Availability, ConnectorRun, Offer, OfferObservation, Product, Source
from app.schemas.catalog import (
    ConnectorRunRead,
    MerchantRef,
    ObservationRead,
    OfferDetailRead,
    OfferPage,
    OfferRead,
    PriceHistoryRead,
    PricePoint,
    SourceRef,
)

CENT = Decimal("0.01")
OfferSort = Literal["recent", "price_eur_asc", "price_eur_desc"]


class NotFoundError(Exception):
    pass


def source_ref(source: Source) -> SourceRef:
    return SourceRef(slug=source.slug, name=source.name, is_demo=source.is_demo)


def price_with_shipping_eur(offer: Offer) -> Decimal | None:
    if offer.price_eur is None or offer.shipping_amount is None or offer.fx_rate_to_eur is None:
        return None
    shipping_eur = offer.shipping_amount * offer.fx_rate_to_eur
    return (offer.price_eur + shipping_eur).quantize(CENT, rounding=ROUND_HALF_UP)


def to_offer_read(offer: Offer, stale_after_hours: int, now: datetime) -> OfferRead:
    return OfferRead(
        id=str(offer.id),
        title=offer.title,
        url=offer.url,
        source=source_ref(offer.source),
        merchant=MerchantRef(name=offer.merchant.name, country=offer.merchant.country)
        if offer.merchant
        else None,
        product_id=str(offer.product_id),
        brand=offer.product.brand,
        gtin=offer.product.gtin,
        mpn=offer.product.mpn,
        size=offer.variant.size or None if offer.variant else None,
        color=offer.variant.color or None if offer.variant else None,
        condition=offer.condition.value,
        country=offer.country,
        price_amount=offer.price_amount,
        currency=offer.currency,
        price_eur=offer.price_eur,
        fx_rate_to_eur=offer.fx_rate_to_eur,
        shipping_amount=offer.shipping_amount,
        price_with_shipping_eur=price_with_shipping_eur(offer),
        availability=offer.availability.value,
        first_seen_at=offer.first_seen_at,
        last_verified_at=offer.last_verified_at,
        is_stale=now - offer.last_verified_at > timedelta(hours=stale_after_hours),
        access_method=offer.access_method.value,
        match_method=offer.match_method.value,
        match_confidence=offer.match_confidence,
        is_demo=offer.is_demo,
    )


def to_observation_read(o: OfferObservation) -> ObservationRead:
    return ObservationRead(
        observed_at=o.observed_at,
        price_amount=o.price_amount,
        currency=o.currency,
        price_eur=o.price_eur,
        shipping_amount=o.shipping_amount,
        availability=o.availability.value,
    )


def escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def offers_query(
    q: str | None,
    brand: str | None,
    source: str | None,
    availability: Availability | None,
    is_demo: bool | None,
    max_price_eur: Decimal | None,
) -> Select[Offer]:
    stmt = select(Offer).join(Offer.product).join(Offer.source)
    if q:
        stmt = stmt.where(Offer.title.ilike(f"%{escape_like(q.strip())}%", escape="\\"))
    if brand:
        stmt = stmt.where(Product.brand_key == brand.strip().casefold())
    if source:
        stmt = stmt.where(Source.slug == source)
    if availability:
        stmt = stmt.where(Offer.availability == availability)
    if is_demo is not None:
        stmt = stmt.where(Offer.is_demo.is_(is_demo))
    if max_price_eur is not None:
        stmt = stmt.where(Offer.price_eur <= max_price_eur)
    return stmt


def list_offers(
    db: Session,
    *,
    stale_after_hours: int,
    limit: int,
    offset: int,
    sort: OfferSort = "recent",
    q: str | None = None,
    brand: str | None = None,
    source: str | None = None,
    availability: Availability | None = None,
    is_demo: bool | None = None,
    max_price_eur: Decimal | None = None,
) -> OfferPage:
    base = offers_query(q, brand, source, availability, is_demo, max_price_eur)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    # Prix EUR inconnu : toujours en fin de liste, jamais assimilé à 0. Tri stable par id.
    primary: UnaryExpression[Any]
    if sort == "price_eur_asc":
        primary = Offer.price_eur.asc().nulls_last()
    elif sort == "price_eur_desc":
        primary = Offer.price_eur.desc().nulls_last()
    else:
        primary = Offer.last_verified_at.desc()
    rows = db.scalars(
        base.options(
            joinedload(Offer.source),
            joinedload(Offer.merchant),
            joinedload(Offer.product),
            joinedload(Offer.variant),
        )
        .order_by(primary, Offer.id)
        .limit(limit)
        .offset(offset)
    ).all()
    now = datetime.now(UTC)
    return OfferPage(
        items=[to_offer_read(o, stale_after_hours, now) for o in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_offer(db: Session, offer_id: uuid.UUID, stale_after_hours: int) -> OfferDetailRead:
    offer = db.get(Offer, offer_id)
    if offer is None:
        raise NotFoundError("Offre introuvable")
    base = to_offer_read(offer, stale_after_hours, datetime.now(UTC))
    return OfferDetailRead(
        **base.model_dump(),
        observations=[to_observation_read(o) for o in offer.observations],
    )


def get_price_history(db: Session, product_id: uuid.UUID) -> PriceHistoryRead:
    product = db.get(Product, product_id)
    if product is None:
        raise NotFoundError("Produit introuvable")
    rows = db.execute(
        select(OfferObservation, Offer)
        .join(Offer, OfferObservation.offer_id == Offer.id)
        .options(joinedload(Offer.merchant), joinedload(Offer.source))
        .where(Offer.product_id == product_id)
        .order_by(OfferObservation.observed_at, OfferObservation.id)
    ).all()
    offer_ids = {offer.id for _, offer in rows}
    return PriceHistoryRead(
        product_id=str(product.id),
        title=product.title,
        brand=product.brand,
        gtin=product.gtin,
        is_demo=product.is_demo,
        offers_count=len(offer_ids),
        points=[
            PricePoint(
                **to_observation_read(obs).model_dump(),
                offer_id=str(offer.id),
                merchant=offer.merchant.name if offer.merchant else None,
                source=offer.source.slug,
            )
            for obs, offer in rows
        ],
    )


def to_run_read(run: ConnectorRun) -> ConnectorRunRead:
    return ConnectorRunRead(
        id=str(run.id),
        source=source_ref(run.source),
        status=run.status.value,
        actor=run.actor,
        started_at=run.started_at,
        finished_at=run.finished_at,
        offers_received=run.offers_received,
        offers_created=run.offers_created,
        offers_updated=run.offers_updated,
        observations_created=run.observations_created,
        errors=list(run.errors),
        is_demo=run.is_demo,
    )


def list_runs(db: Session, limit: int) -> list[ConnectorRunRead]:
    runs = db.scalars(
        select(ConnectorRun)
        .options(joinedload(ConnectorRun.source))
        .order_by(ConnectorRun.started_at.desc(), ConnectorRun.id)
        .limit(limit)
    ).all()
    return [to_run_read(r) for r in runs]
