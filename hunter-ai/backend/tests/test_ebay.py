"""Connecteur eBay Browse API : réponses simulées d'après la documentation officielle.

Aucun appel réseau réel. Le test réel se fait avec vos identifiants via « Tester la connexion ».
"""

import base64
from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors import ebay
from app.connectors.base import ConnectorError, SearchQuery
from app.connectors.ebay import EbayConnector, condition_from_id, to_raw_offer
from app.core.config import Settings, get_settings
from app.models import AuditLog, ConnectorRun, Offer, Source, SourceStatus
from app.services import connector_service
from app.services.collection_service import CollectionRefusedError, run_bounded

CONFIGURED = Settings(ebay_client_id="app-id", ebay_client_secret="cert-secret")

ITEM = {
    "itemId": "v1|123|0",
    "title": "Polo Ralph Lauren homme taille M",
    "price": {"value": "24.90", "currency": "EUR"},
    "conditionId": "3000",
    "itemWebUrl": "https://www.ebay.fr/itm/123",
    "itemAffiliateWebUrl": "https://www.ebay.fr/itm/123?affiliate",
    "itemLocation": {"country": "FR", "postalCode": "75***"},
    "categories": [{"categoryId": "185100", "categoryName": "Polos"}],
    "seller": {"username": "particulier75", "feedbackPercentage": "99.1", "feedbackScore": 12},
    "shippingOptions": [
        {"shippingCostType": "FIXED", "shippingCost": {"value": "4.50", "currency": "EUR"}}
    ],
}


@pytest.fixture(autouse=True)
def clear_token_cache():
    ebay._token_cache.clear()
    yield
    ebay._token_cache.clear()


class FakeEbay:
    """Simule les deux points d'accès eBay et enregistre les requêtes reçues."""

    def __init__(self, search_status=200, token_status=200, items=None):
        self.search_status = search_status
        self.token_status = token_status
        self.items = [ITEM] if items is None else items
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.url.path == "/identity/v1/oauth2/token":
            if self.token_status != 200:
                return httpx.Response(self.token_status, json={"error": "invalid_client"})
            return httpx.Response(200, json={"access_token": "TOKEN", "expires_in": 7200})
        if request.url.path == "/buy/browse/v1/item_summary/search":
            if self.search_status != 200:
                return httpx.Response(
                    self.search_status,
                    json={"errors": [{"errorId": 1100, "message": "Access denied"}]},
                )
            return httpx.Response(200, json={"total": len(self.items), "itemSummaries": self.items})
        return httpx.Response(404)

    def connector(self, settings: Settings = CONFIGURED) -> EbayConnector:
        return EbayConnector(settings, transport=httpx.MockTransport(self))


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("1000", "new"),
        ("1500", "unknown"),
        ("2010", "refurbished"),
        ("3000", "used"),
        ("7000", "unknown"),
        (None, "unknown"),
        ("abc", "unknown"),
    ],
)
def test_condition_mapping_is_conservative(code, expected):
    assert condition_from_id(code) == expected


def test_item_mapping():
    now = datetime(2026, 11, 24, 6, 0, tzinfo=UTC)
    raw = to_raw_offer(ITEM, now)
    assert raw is not None
    assert (raw.external_id, raw.price, raw.currency) == ("v1|123|0", Decimal("24.90"), "EUR")
    assert raw.url == "https://www.ebay.fr/itm/123"  # lien public, pas l'affiliation
    assert raw.shipping_cost == Decimal("4.50")
    assert raw.condition == "used" and raw.availability == "unknown"
    assert raw.merchant_name is None  # vendeur non enregistré
    calculated = {**ITEM, "shippingOptions": [{"shippingCostType": "CALCULATED"}]}
    assert to_raw_offer(calculated, now).shipping_cost is None  # inconnu, pas 0
    other_currency = {
        **ITEM,
        "shippingOptions": [
            {"shippingCostType": "FIXED", "shippingCost": {"value": "3", "currency": "GBP"}}
        ],
    }
    assert to_raw_offer(other_currency, now).shipping_cost is None
    assert to_raw_offer({**ITEM, "price": {}}, now) is None


def test_search_params():
    c = EbayConnector(CONFIGURED)
    params = c.search_params(
        SearchQuery(keywords="polo", brand="Ralph Lauren", max_price=Decimal("30"), limit=500)
    )
    assert params["sort"] == "newlyListed"
    assert params["limit"] == "200"
    assert params["q"] == "Ralph Lauren polo"
    assert params["filter"] == (
        "buyingOptions:{FIXED_PRICE},deliveryCountry:FR,price:[..30],priceCurrency:EUR"
    )
    assert c.search_params(SearchQuery(gtin="2000000000015"))["gtin"] == "2000000000015"
    with pytest.raises(ConnectorError):
        c.search_params(SearchQuery())


def test_search_sends_documented_requests_and_reuses_token():
    fake = FakeEbay()
    c = fake.connector()
    offers = run_bounded(c.search(SearchQuery(keywords="polo")))
    assert len(offers) == 1 and c.api_calls == 2
    token_req, search_req = fake.requests
    assert token_req.method == "POST"
    expected = base64.b64encode(b"app-id:cert-secret").decode()
    assert token_req.headers["Authorization"] == f"Basic {expected}"
    assert b"grant_type=client_credentials" in token_req.content
    assert b"scope=https%3A%2F%2Fapi.ebay.com%2Foauth%2Fapi_scope" in token_req.content
    assert search_req.headers["Authorization"] == "Bearer TOKEN"
    assert search_req.headers["X-EBAY-C-MARKETPLACE-ID"] == "EBAY_FR"
    assert str(search_req.url).startswith("https://api.ebay.com/buy/browse/v1/item_summary/search")
    # Deuxième recherche : jeton en cache, un seul appel.
    c2 = fake.connector()
    run_bounded(c2.search(SearchQuery(keywords="polo")))
    assert c2.api_calls == 1


def test_sandbox_uses_sandbox_host():
    fake = FakeEbay()
    settings = Settings(ebay_client_id="a", ebay_client_secret="b", ebay_environment="sandbox")
    run_bounded(fake.connector(settings).search(SearchQuery(keywords="x")))
    assert all(r.url.host == "api.sandbox.ebay.com" for r in fake.requests)


@pytest.mark.parametrize(
    ("fake", "message"),
    [
        (FakeEbay(search_status=403), "refusé"),
        (FakeEbay(token_status=401), "identifiants"),
        (FakeEbay(search_status=429), "Quota"),
        (FakeEbay(search_status=500), "HTTP 500"),
    ],
)
def test_errors_are_explicit(fake, message):
    with pytest.raises(ConnectorError, match=message):
        run_bounded(fake.connector().search(SearchQuery(keywords="x")))


def test_unconfigured_connector_is_unhealthy_without_network():
    fake = FakeEbay()
    health = run_bounded(fake.connector(Settings()).health_check())
    assert health.ok is False and "non configurés" in health.detail
    assert fake.requests == []


# --- Services : test de connexion, collecte, quotas ---------------------------------------


def use_fake(monkeypatch, fake: FakeEbay) -> None:
    monkeypatch.setattr(
        connector_service, "get_connector", lambda slug, settings: fake.connector(settings)
    )


def test_successful_real_test_activates_source(db: Session, monkeypatch):
    use_fake(monkeypatch, FakeEbay())
    result = connector_service.test_source(db, "ebay", "test", CONFIGURED)
    assert result.ok and result.status == "active" and result.api_calls == 2
    source = db.scalars(select(Source).where(Source.slug == "ebay")).one()
    assert source.status == SourceStatus.active
    assert "Dernier test réussi" in (source.terms_notes or "")
    assert db.scalars(select(AuditLog).where(AuditLog.action == "source.test")).one()
    assert db.scalars(select(Offer)).all() == []  # le test n'enregistre aucune offre


@pytest.mark.parametrize(
    ("fake", "settings", "status"),
    [
        (FakeEbay(search_status=403), CONFIGURED, SourceStatus.needs_approval),
        (FakeEbay(token_status=401), CONFIGURED, SourceStatus.needs_credentials),
        (FakeEbay(), Settings(), SourceStatus.needs_credentials),
        (FakeEbay(search_status=500), CONFIGURED, SourceStatus.error),
    ],
)
def test_failed_test_never_activates(db: Session, monkeypatch, fake, settings, status):
    use_fake(monkeypatch, fake)
    result = connector_service.test_source(db, "ebay", "test", settings)
    assert result.ok is False and result.status == status.value


def test_collect_requires_successful_test_then_stores_offers(db: Session, monkeypatch):
    use_fake(monkeypatch, FakeEbay())
    with pytest.raises(CollectionRefusedError):
        connector_service.collect_from_source(
            db, "ebay", SearchQuery(keywords="polo"), "test", CONFIGURED
        )
    connector_service.test_source(db, "ebay", "test", CONFIGURED)
    run = connector_service.collect_from_source(
        db, "ebay", SearchQuery(keywords="polo"), "test", CONFIGURED
    )
    assert run.offers_created == 1 and run.api_calls == 1  # jeton déjà en cache
    offer = db.scalars(select(Offer)).one()
    assert offer.access_method.value == "official_api" and offer.is_demo is False
    assert offer.merchant_id is None and offer.price_eur == Decimal("24.90")


def test_daily_call_budget_is_enforced(db: Session, monkeypatch):
    use_fake(monkeypatch, FakeEbay())
    tight = Settings(ebay_client_id="a", ebay_client_secret="b", ebay_daily_call_budget=3)
    connector_service.test_source(db, "ebay", "test", tight)  # 2 appels consommés
    with pytest.raises(CollectionRefusedError, match="Quota journalier"):
        connector_service.collect_from_source(db, "ebay", SearchQuery(keywords="x"), "t", tight)
    assert sum(r.api_calls for r in db.scalars(select(ConnectorRun)).all()) == 2


# --- API -----------------------------------------------------------------------------------


def test_connectors_listing(client):
    rows = {c["slug"]: c for c in client.get("/api/v1/connectors").json()}
    assert set(rows) == {"demo", "ebay"}
    assert rows["ebay"]["configured"] is False and rows["ebay"]["status"] is None
    assert rows["ebay"]["daily_call_budget"] == 4500


def test_api_test_and_collect_guards(client, monkeypatch):
    from app.main import app

    app.dependency_overrides[get_settings] = lambda: Settings()
    try:
        res = client.post("/api/v1/sources/ebay/test").json()
        assert res["ok"] is False and res["status"] == "needs_credentials"
        assert client.post("/api/v1/sources/inconnue/test").status_code == 409
        collect = client.post("/api/v1/sources/ebay/collect", json={"keywords": "polo"})
        assert collect.status_code == 409
        bad = client.post("/api/v1/sources/ebay/collect", json={"gtin": "abc"})
        assert bad.status_code == 422
        extra = client.post("/api/v1/sources/ebay/collect", json={"keywords": "x", "hack": 1})
        assert extra.status_code == 422
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_api_full_flow_with_simulated_ebay(client, monkeypatch):
    from app.main import app

    use_fake(monkeypatch, FakeEbay())
    app.dependency_overrides[get_settings] = lambda: CONFIGURED
    try:
        assert client.post("/api/v1/sources/ebay/test").json()["status"] == "active"
        run = client.post(
            "/api/v1/sources/ebay/collect", json={"keywords": "polo", "max_price": "30"}
        ).json()
        assert run["status"] == "success" and run["offers_created"] == 1
        offers = client.get("/api/v1/offers", params={"source": "ebay"}).json()
        assert offers["total"] == 1 and offers["items"][0]["is_demo"] is False
        status = client.get("/api/v1/system/status").json()["components"]
        connectors = next(c for c in status if c["name"] == "Connecteurs de données")
        assert connectors["status"] == "ok"
    finally:
        app.dependency_overrides.pop(get_settings, None)
