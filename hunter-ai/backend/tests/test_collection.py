"""Collecte : déduplication, idempotence, historique, rattachement produit, pannes de connecteur."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.connectors.base import (
    ConnectorError,
    RawOffer,
    SearchQuery,
    SourceCapabilities,
    SourceConnector,
    SourceHealth,
)
from app.connectors.demo import DemoConnector
from app.models import (
    AccessMethod,
    AuditLog,
    MatchMethod,
    Offer,
    OfferObservation,
    Product,
    RunStatus,
    Source,
    SourceStatus,
)
from app.services.collection_service import CollectionRefusedError, run_collection
from app.services.demo_service import load_demo


def count(db: Session, model: type) -> int:
    return db.scalar(select(func.count()).select_from(model)) or 0


def offer(db: Session, external_id: str) -> Offer:
    return db.scalars(select(Offer).where(Offer.external_id == external_id)).one()


class StubConnector:
    """Connecteur de test renvoyant des offres choisies ou une panne."""

    source_slug = "stub"

    def __init__(self, offers: list[RawOffer] | None = None, error: Exception | None = None):
        self.offers = offers or []
        self.error = error

    async def health_check(self) -> SourceHealth:
        return SourceHealth(ok=True, detail="ok")

    async def get_capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            access_method=AccessMethod.official_api,
            supports_search=True,
            supports_fetch_offer=False,
            supports_gtin_search=False,
            max_results_per_query=10,
            min_interval_seconds=0,
            is_demo=False,
        )

    async def search(self, query: SearchQuery) -> list[RawOffer]:
        if self.error:
            raise self.error
        return self.offers

    async def fetch_offer(self, external_id: str) -> RawOffer | None:
        return None


def raw(external_id: str, **over: object) -> RawOffer:
    fields: dict[str, object] = {
        "external_id": external_id,
        "title": f"Article {external_id}",
        "url": f"https://example.com/{external_id}",
        "price": Decimal("10.00"),
        "currency": "EUR",
        "observed_at": datetime(2026, 11, 24, 6, 0, tzinfo=UTC),
    }
    fields.update(over)
    return RawOffer(**fields)  # type: ignore[arg-type]


@pytest.fixture
def stub_source(db: Session) -> Source:
    source = Source(slug="stub", name="Source test", family="api", status=SourceStatus.active)
    db.add(source)
    db.commit()
    return source


def collect(db: Session, source: Source, connector: SourceConnector):
    return run_collection(db, source, connector, SearchQuery(), "test", rates_to_eur={})


def test_stub_connector_respects_contract():
    assert isinstance(StubConnector(), SourceConnector)
    assert isinstance(DemoConnector(), SourceConnector)


def test_demo_load_creates_traceable_demo_offers(db: Session):
    run = load_demo(db, "test")
    assert run.status == RunStatus.success
    assert (run.offers_received, run.offers_created, run.observations_created) == (6, 6, 6)
    offers = db.scalars(select(Offer)).all()
    assert all(o.is_demo and o.title.startswith("[DEMO]") for o in offers)
    assert all(o.url.startswith("https://example.com/demo/") for o in offers)
    assert all(o.last_verified_at.tzinfo is not None for o in offers)
    # Prix EUR connu pour les offres en euros, « non déterminé » pour USD/GBP sans taux configuré.
    assert offer(db, "D-001").price_eur == Decimal("59.90")
    assert offer(db, "D-005").price_eur is None
    assert offer(db, "D-006").price_eur is None
    # Frais de livraison : inconnus (None) ≠ gratuits (0).
    assert offer(db, "D-002").shipping_amount is None
    assert offer(db, "D-003").shipping_amount == Decimal("0.00")


def test_products_matched_by_gtin_then_brand_mpn_never_by_title(db: Session):
    load_demo(db, "test")
    d1, d2, d3, d4, d5 = (offer(db, f"D-00{i}") for i in range(1, 6))
    assert d1.product_id == d2.product_id  # même GTIN, titres différents
    assert d2.match_method == MatchMethod.gtin
    assert d3.product_id == d4.product_id  # même marque + référence, casse différente
    assert d4.match_method == MatchMethod.brand_mpn
    assert d4.match_confidence == Decimal("0.90")
    assert d5.match_method == MatchMethod.new_product
    assert count(db, Product) == 4


def test_same_title_without_identifiers_is_not_merged(db: Session, stub_source: Source):
    collect(
        db, stub_source, StubConnector([raw("A", title="Polo bleu"), raw("B", title="Polo bleu")])
    )
    assert count(db, Product) == 2


def test_same_brand_mpn_but_different_gtin_stays_separate(db: Session, stub_source: Source):
    run = collect(
        db,
        stub_source,
        StubConnector(
            [
                raw("A", brand="Marque", mpn="X1", gtin="2000000000015"),
                raw("B", brand="Marque", mpn="X1", gtin="2000000000022"),
            ]
        ),
    )
    assert run.status == RunStatus.success
    assert offer(db, "A").product_id != offer(db, "B").product_id


def test_repeated_collection_is_idempotent(db: Session):
    load_demo(db, "test")
    first_check = offer(db, "D-001").last_verified_at
    run = load_demo(db, "test")
    assert (run.offers_created, run.offers_updated, run.observations_created) == (0, 6, 0)
    assert count(db, Offer) == 6
    assert count(db, OfferObservation) == 6
    assert offer(db, "D-001").last_verified_at >= first_check


def test_price_change_adds_an_observation(db: Session):
    load_demo(db, "test")
    run = load_demo(db, "test", DemoConnector(revision=2))
    assert run.observations_created == 1
    d1 = offer(db, "D-001")
    assert d1.price_amount == Decimal("49.90")
    assert [o.price_amount for o in d1.observations] == [Decimal("59.90"), Decimal("49.90")]


def test_invalid_offer_is_skipped_without_blocking_others(db: Session, stub_source: Source):
    run = collect(
        db,
        stub_source,
        StubConnector([raw("OK"), raw("BAD", currency="EURO"), raw("NOURL", url="ftp://x")]),
    )
    assert run.status == RunStatus.partial
    assert run.offers_created == 1
    assert len(run.errors) == 2 and "BAD" in run.errors[0]
    assert count(db, Offer) == 1


@pytest.mark.parametrize(
    "error", [ConnectorError("Quota atteint"), RuntimeError("bug"), TimeoutError()]
)
def test_connector_failure_is_recorded_not_raised(db: Session, stub_source: Source, error):
    load_demo(db, "test")
    run = collect(db, stub_source, StubConnector(error=error))
    assert run.status == RunStatus.error
    assert run.errors and run.finished_at is not None
    db.refresh(stub_source)
    assert stub_source.status == SourceStatus.error
    # Les autres sources et leurs données ne sont pas touchées.
    assert count(db, Offer) == 6
    audit = db.scalars(select(AuditLog).where(AuditLog.action == "collection.run")).all()
    assert any(a.details["status"] == "error" for a in audit)


def test_unhealthy_source_is_an_error_run(db: Session):
    run = load_demo(db, "test", DemoConnector(fail=True))
    assert run.status == RunStatus.error
    assert "indisponible" in run.errors[0]
    assert count(db, Offer) == 0


@pytest.mark.parametrize(
    "status",
    [
        SourceStatus.planned,
        SourceStatus.needs_approval,
        SourceStatus.blocked_by_terms,
        SourceStatus.disabled,
        SourceStatus.needs_credentials,
    ],
)
def test_unauthorized_source_never_collects(db: Session, stub_source: Source, status):
    stub_source.status = status
    db.commit()
    with pytest.raises(CollectionRefusedError):
        collect(db, stub_source, StubConnector([raw("A")]))
    assert count(db, Offer) == 0


def test_conversion_uses_configured_rate(db: Session, stub_source: Source):
    run_collection(
        db,
        stub_source,
        StubConnector([raw("U", currency="usd", price=Decimal("20"), shipping_cost=Decimal("5"))]),
        SearchQuery(),
        "test",
        rates_to_eur={"USD": Decimal("0.9")},
    )
    o = offer(db, "U")
    assert (o.currency, o.price_eur, o.fx_rate_to_eur) == ("USD", Decimal("18.00"), Decimal("0.9"))
