"""Collecte : exécute un connecteur, normalise, rattache aux produits, déduplique, historise.

Garanties :
- une source non autorisée (statut ≠ active/degraded/error) ne collecte jamais ;
- une offre invalide est écartée et consignée, sans bloquer les autres (exécution « partial ») ;
- une panne du connecteur est consignée (exécution « error ») et ne lève pas d'exception ;
- une collecte répétée avec les mêmes données ne crée ni doublon d'offre ni observation
  supplémentaire : seule la date de dernière vérification avance (idempotence).
"""

import asyncio
import logging
from collections.abc import Awaitable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.base import ConnectorError, RawOffer, SearchQuery, SourceConnector
from app.models import (
    AccessMethod,
    Availability,
    Condition,
    ConnectorRun,
    MatchMethod,
    Merchant,
    Offer,
    OfferObservation,
    Product,
    ProductVariant,
    RunStatus,
    Source,
    SourceStatus,
)
from app.services.audit import record_audit
from app.services.normalization import (
    NormalizationError,
    clean_text,
    convert_to_eur,
    normalize_amount,
    normalize_availability,
    normalize_condition,
    normalize_country,
    normalize_currency,
    normalize_gtin,
    normalize_url,
    text_key,
    to_utc,
)

logger = logging.getLogger("hunter.collection")

COLLECTABLE_STATUSES = {SourceStatus.active, SourceStatus.degraded, SourceStatus.error}
CONNECTOR_TIMEOUT_SECONDS = 60
MAX_ERRORS_KEPT = 50

CONFIDENCE = {
    MatchMethod.gtin: Decimal("1.00"),
    MatchMethod.brand_mpn: Decimal("0.90"),
    # Produit créé pour cette seule offre : aucun rapprochement n'a été tenté sur le titre.
    MatchMethod.new_product: Decimal("1.00"),
}


class CollectionRefusedError(Exception):
    """La source n'est pas autorisée à collecter (statut ou connecteur absent)."""


@dataclass(frozen=True)
class NormalizedOffer:
    external_id: str
    title: str
    url: str
    price: Decimal
    currency: str
    price_eur: Decimal | None
    fx_rate: Decimal | None
    shipping: Decimal | None
    observed_at: datetime
    availability: Availability
    condition: Condition
    country: str | None
    merchant_name: str | None
    merchant_country: str | None
    brand: str | None
    brand_key: str | None
    model: str | None
    mpn: str | None
    gtin: str | None
    category: str | None
    size: str
    color: str


def normalize_offer(raw: RawOffer, rates_to_eur: dict[str, Decimal]) -> NormalizedOffer:
    external_id = clean_text(raw.external_id, 200)
    title = clean_text(raw.title, 500)
    if not external_id or not title:
        raise NormalizationError("Identifiant externe ou titre absent")
    currency = normalize_currency(raw.currency)
    price = normalize_amount(raw.price, required=True)
    if price is None:  # impossible avec required=True ; garde explicite pour le typage
        raise NormalizationError("Prix absent")
    shipping = normalize_amount(raw.shipping_cost)
    price_eur, rate = convert_to_eur(price, currency, rates_to_eur)
    brand = clean_text(raw.brand, 120)
    mpn = clean_text(raw.mpn, 120)
    return NormalizedOffer(
        external_id=external_id,
        title=title,
        url=normalize_url(raw.url),
        price=price,
        currency=currency,
        price_eur=price_eur,
        fx_rate=rate,
        shipping=shipping,
        observed_at=to_utc(raw.observed_at),
        availability=normalize_availability(raw.availability),
        condition=normalize_condition(raw.condition),
        country=normalize_country(raw.country),
        merchant_name=clean_text(raw.merchant_name, 200),
        merchant_country=normalize_country(raw.merchant_country),
        brand=brand,
        brand_key=text_key(brand),
        model=clean_text(raw.model, 200),
        mpn=mpn.upper() if mpn else None,
        gtin=normalize_gtin(raw.gtin),
        category=clean_text(raw.category, 200),
        size=clean_text(raw.size, 40) or "",
        color=clean_text(raw.color, 80) or "",
    )


def match_product(db: Session, n: NormalizedOffer, is_demo: bool) -> tuple[Product, MatchMethod]:
    """Rattache l'offre à un produit par GTIN, puis par marque + référence fabricant.

    Jamais par ressemblance de titre (cahier des charges §3.1).
    """
    if n.gtin:
        product = db.scalar(select(Product).where(Product.gtin == n.gtin))
        if product:
            return product, MatchMethod.gtin
    if n.brand_key and n.mpn:
        product = db.scalar(
            select(Product).where(Product.brand_key == n.brand_key, Product.mpn == n.mpn)
        )
        # Même marque + référence mais GTIN différent : ce n'est pas forcément le même article.
        if product and (product.gtin is None or n.gtin is None or product.gtin == n.gtin):
            if product.gtin is None and n.gtin:
                product.gtin = n.gtin
            return product, MatchMethod.brand_mpn
    mpn_taken = bool(
        n.brand_key
        and n.mpn
        and db.scalar(
            select(Product.id).where(Product.brand_key == n.brand_key, Product.mpn == n.mpn)
        )
    )
    product = Product(
        title=n.title,
        brand=n.brand,
        brand_key=n.brand_key,
        model=n.model,
        mpn=None if mpn_taken else n.mpn,
        gtin=n.gtin,
        category=n.category,
        is_demo=is_demo,
    )
    db.add(product)
    db.flush()
    return product, MatchMethod.new_product


def get_or_create_variant(db: Session, product: Product, size: str, color: str) -> ProductVariant:
    variant = db.scalar(
        select(ProductVariant).where(
            ProductVariant.product_id == product.id,
            ProductVariant.size == size,
            ProductVariant.color == color,
        )
    )
    if variant is None:
        variant = ProductVariant(product_id=product.id, size=size, color=color)
        db.add(variant)
        db.flush()
    return variant


def get_or_create_merchant(
    db: Session, name: str | None, country: str | None, is_demo: bool
) -> Merchant | None:
    if not name:
        return None
    key = f"{text_key(name)}|{country or ''}"
    merchant = db.scalar(select(Merchant).where(Merchant.key == key))
    if merchant is None:
        merchant = Merchant(key=key, name=name, country=country, is_demo=is_demo)
        db.add(merchant)
        db.flush()
    return merchant


def observation_changed(last: OfferObservation | None, n: NormalizedOffer) -> bool:
    if last is None:
        return True
    return (last.price_amount, last.currency, last.shipping_amount, last.availability) != (
        n.price,
        n.currency,
        n.shipping,
        n.availability,
    )


def upsert_offer(
    db: Session,
    source: Source,
    run: ConnectorRun,
    n: NormalizedOffer,
    access_method: AccessMethod,
) -> tuple[bool, bool]:
    """Enregistre une offre normalisée. Renvoie (offre créée, observation créée)."""
    product, method = match_product(db, n, source.is_demo)
    variant = get_or_create_variant(db, product, n.size, n.color) if (n.size or n.color) else None
    merchant = get_or_create_merchant(db, n.merchant_name, n.merchant_country, source.is_demo)

    offer = db.scalar(
        select(Offer).where(Offer.source_id == source.id, Offer.external_id == n.external_id)
    )
    created = offer is None
    if offer is None:
        offer = Offer(
            source_id=source.id,
            external_id=n.external_id,
            first_seen_at=n.observed_at,
            is_demo=source.is_demo,
        )
        db.add(offer)
    offer.product_id = product.id
    offer.variant_id = variant.id if variant else None
    offer.merchant_id = merchant.id if merchant else None
    offer.title = n.title
    offer.url = n.url
    offer.condition = n.condition
    offer.country = n.country
    offer.price_amount = n.price
    offer.currency = n.currency
    offer.price_eur = n.price_eur
    offer.fx_rate_to_eur = n.fx_rate
    offer.shipping_amount = n.shipping
    offer.availability = n.availability
    offer.access_method = access_method
    offer.match_method = method
    offer.match_confidence = CONFIDENCE[method]
    offer.last_seen_at = n.observed_at
    offer.last_verified_at = n.observed_at
    db.flush()

    last = db.scalar(
        select(OfferObservation)
        .where(OfferObservation.offer_id == offer.id)
        .order_by(OfferObservation.observed_at.desc())
        .limit(1)
    )
    observed = observation_changed(last, n)
    if observed:
        db.add(
            OfferObservation(
                offer_id=offer.id,
                run_id=run.id,
                observed_at=n.observed_at,
                price_amount=n.price,
                currency=n.currency,
                price_eur=n.price_eur,
                shipping_amount=n.shipping,
                availability=n.availability,
            )
        )
        db.flush()
    return created, observed


def run_bounded[T](coro: Awaitable[T]) -> T:
    async def bounded() -> T:
        return await asyncio.wait_for(coro, timeout=CONNECTOR_TIMEOUT_SECONDS)

    return asyncio.run(bounded())


def fetch_raw_offers(connector: SourceConnector, query: SearchQuery) -> list[RawOffer]:
    health = run_bounded(connector.health_check())
    if not health.ok:
        raise ConnectorError(f"Source indisponible : {health.detail}")
    return run_bounded(connector.search(query))


def run_collection(
    db: Session,
    source: Source,
    connector: SourceConnector,
    query: SearchQuery,
    actor: str,
    rates_to_eur: dict[str, Decimal],
) -> ConnectorRun:
    if source.status not in COLLECTABLE_STATUSES:
        raise CollectionRefusedError(
            f"La source « {source.name} » n'est pas autorisée à collecter "
            f"(statut : {source.status.value})."
        )
    query_log: dict[str, Any] = {k: str(v) for k, v in asdict(query).items() if v not in (None, "")}
    run = ConnectorRun(source_id=source.id, actor=actor, query=query_log, is_demo=source.is_demo)
    db.add(run)
    db.flush()

    errors: list[str] = []
    accepted = 0
    try:
        capabilities = run_bounded(connector.get_capabilities())
        raw_offers = fetch_raw_offers(connector, query)
    except Exception as exc:  # une panne de connecteur, quelle qu'elle soit, est consignée
        if isinstance(exc, ConnectorError | TimeoutError):
            message = str(exc) or "Délai dépassé"
        else:
            message = f"Erreur inattendue du connecteur ({type(exc).__name__})"
            logger.exception("erreur inattendue du connecteur", extra={"source": source.slug})
        logger.warning("connecteur en erreur", extra={"source": source.slug, "error": message})
        run.status = RunStatus.error
        run.errors = [message]
        source.status = SourceStatus.error
    else:
        run.offers_received = len(raw_offers)
        for raw in raw_offers:
            try:
                with db.begin_nested():
                    normalized = normalize_offer(raw, rates_to_eur)
                    created, observed = upsert_offer(
                        db, source, run, normalized, capabilities.access_method
                    )
            except NormalizationError as exc:
                errors.append(f"{raw.external_id or '?'} : {exc}")
                continue
            accepted += 1
            run.offers_created += int(created)
            run.offers_updated += int(not created)
            run.observations_created += int(observed)
        if errors and accepted == 0:
            run.status = RunStatus.error
        elif errors:
            run.status = RunStatus.partial
        else:
            run.status = RunStatus.success
        run.errors = errors[:MAX_ERRORS_KEPT]
        source.status = SourceStatus.active if accepted or not errors else SourceStatus.degraded

    run.api_calls = int(getattr(connector, "api_calls", 0))
    run.finished_at = datetime.now(UTC)
    record_audit(
        db,
        actor=actor,
        action="collection.run",
        entity_type="source",
        entity_id=source.id,
        details={
            "run_id": str(run.id),
            "status": run.status.value,
            "received": run.offers_received,
            "created": run.offers_created,
            "updated": run.offers_updated,
            "observations": run.observations_created,
            "errors": len(run.errors),
            "api_calls": run.api_calls,
        },
    )
    db.commit()
    db.refresh(run)
    return run
