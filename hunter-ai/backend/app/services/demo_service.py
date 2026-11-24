"""Données de démonstration : chargement explicite et suppression complète (réversible)."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.connectors.base import SearchQuery
from app.connectors.demo import DEMO_SLUG, DemoConnector
from app.models import (
    AccessMethod,
    ConnectorRun,
    Merchant,
    Offer,
    Product,
    Source,
    SourceStatus,
)
from app.schemas.catalog import DemoPurgeRead
from app.services.audit import record_audit
from app.services.collection_service import run_collection


def get_or_create_demo_source(db: Session) -> Source:
    source = db.scalar(select(Source).where(Source.slug == DEMO_SLUG))
    if source is None:
        source = Source(
            slug=DEMO_SLUG,
            name="Source DEMO (données fictives)",
            family="demo",
            access_method=AccessMethod.manual_import,
            # Connecteur local testé automatiquement ; ses données sont toutes marquées DEMO.
            status=SourceStatus.active,
            terms_notes="Données inventées, aucun accès externe. Ne reflètent aucun prix réel.",
            is_demo=True,
        )
        db.add(source)
        db.flush()
    return source


def load_demo(db: Session, actor: str, connector: DemoConnector | None = None) -> ConnectorRun:
    source = get_or_create_demo_source(db)
    return run_collection(
        db,
        source,
        connector or DemoConnector(),
        SearchQuery(),
        actor,
        # Les offres DEMO en USD/GBP restent volontairement sans conversion EUR : elles montrent
        # l'affichage « non déterminé » quand aucun taux n'est configuré.
        rates_to_eur={},
    )


def purge_demo(db: Session, actor: str) -> DemoPurgeRead:
    def delete_demo_rows(model: type[Offer | Product | Merchant | ConnectorRun | Source]) -> int:
        ids = db.scalars(select(model.id).where(model.is_demo.is_(True))).all()
        db.execute(delete(model).where(model.id.in_(ids)))
        return len(ids)

    # Ordre : offres (et leurs observations en cascade), puis ce qui n'est plus référencé.
    offers = delete_demo_rows(Offer)
    products = delete_demo_rows(Product)
    merchants = delete_demo_rows(Merchant)
    delete_demo_rows(ConnectorRun)
    sources = delete_demo_rows(Source)
    result = DemoPurgeRead(
        offers_deleted=offers,
        products_deleted=products,
        merchants_deleted=merchants,
        sources_deleted=sources,
    )
    record_audit(
        db, actor=actor, action="demo.purge", entity_type="source", details=result.model_dump()
    )
    db.commit()
    return result
