"""Connecteur AliExpress Affiliate : signature (vecteurs officiels), requêtes, réponses simulées."""

from datetime import UTC, datetime
from decimal import Decimal
from urllib.parse import parse_qs

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.aliexpress import (
    METHOD,
    AliExpressConnector,
    products_from,
    sign_params,
    to_raw_offer,
)
from app.connectors.base import ConnectorError, SearchQuery
from app.core.config import Settings
from app.models import Offer, Source, SourceStatus
from app.services import connector_service
from app.services.collection_service import run_bounded

CONFIGURED = Settings(aliexpress_app_key="123456", aliexpress_app_secret="helloworld")
NOW = datetime(2026, 11, 24, 6, 0, tzinfo=UTC)

PRODUCT = {
    "product_id": "1005001",
    "product_title": "Coque iPhone 16 antichoc",
    "target_sale_price": "1.89",
    "target_sale_price_currency": "EUR",
    "sale_price": "2.05",
    "sale_price_currency": "USD",
    "product_detail_url": "https://www.aliexpress.com/item/1005001.html",
    "promotion_link": "https://s.click.aliexpress.com/e/_affiliate",
    "shop_name": "Case Factory Store",
    "evaluate_rate": "96.5%",
    "lastest_volume": "1200",
    "second_level_category_name": "Coques de téléphone",
}


def envelope(products, full=True):
    result = {
        "resp_code": "200",
        "resp_msg": "success",
        "result": {"products": {"product": products} if full else products},
    }
    if full:
        return {"aliexpress_affiliate_product_query_response": {"resp_result": result}}
    return {"resp_result": result}


def test_official_signature_vectors():
    # Exemples officiels AliExpress (secret « helloworld »), appel métier et appel système.
    business = {
        "method": "aliexpress.logistics.redefining.getonlinelogisticsinfo",
        "aliexpress_category_id": "200135143",
        "app_key": "123456",
        "sign_method": "sha256",
        "access_token": "test",
        "timestamp": "1517820392000",
    }
    assert sign_params(business, "helloworld") == (
        "F7F7926B67316C9D1E8E15F7E66940ED3059B1638C497D77973F30046EFB5BBB"
    )
    system = {
        "app_key": "12345678",
        "code": "3_500102_JxZ05Ux3cnnSSUm6dCxYg6Q26",
        "sign_method": "sha256",
        "timestamp": "1517820392000",
    }
    assert sign_params(system, "helloworld", "/auth/token/create") == (
        "35607762342831B6A417A0DED84B79C05FEFBF116969C48AD6DC00279A9F4D81"
    )
    # Le paramètre « sign » et les valeurs vides ne sont pas signés.
    assert sign_params({**system, "sign": "X", "uuid": ""}, "helloworld", "/auth/token/create") == (
        sign_params(system, "helloworld", "/auth/token/create")
    )


def test_request_parameters_are_signed_and_target_france():
    c = AliExpressConnector(CONFIGURED)
    params = c.signed_params(c.business_params(SearchQuery(keywords="coque iphone", limit=500)))
    assert params["method"] == METHOD and params["sign_method"] == "sha256"
    assert (params["target_currency"], params["target_language"], params["ship_to_country"]) == (
        "EUR",
        "FR",
        "FR",
    )
    assert params["page_size"] == "50"
    assert "tracking_id" not in params  # vide : non envoyé
    assert len(params["timestamp"]) == 13  # millisecondes
    unsigned = {k: v for k, v in params.items() if k != "sign"}
    assert params["sign"] == sign_params(unsigned, "helloworld")
    assert "helloworld" not in str(params)  # le secret ne part jamais dans la requête
    with pytest.raises(ConnectorError):
        c.business_params(SearchQuery())


def test_mapping():
    raw = to_raw_offer(PRODUCT, NOW)
    assert (raw.price, raw.currency) == (Decimal("1.89"), "EUR")
    assert raw.url == "https://www.aliexpress.com/item/1005001.html"  # pas le lien d'affiliation
    assert raw.merchant_name == "Case Factory Store"
    assert raw.shipping_cost is None and raw.availability == "unknown"
    assert raw.extra["lastest_volume"] == "1200"
    fallback = to_raw_offer({**PRODUCT, "target_sale_price": None}, NOW)
    assert (fallback.price, fallback.currency) == (Decimal("2.05"), "USD")
    assert to_raw_offer({**PRODUCT, "product_detail_url": ""}, NOW) is None


def test_envelopes_and_errors():
    assert len(products_from(envelope([PRODUCT]))) == 1
    assert len(products_from(envelope([PRODUCT], full=False))) == 1
    assert products_from({"resp_result": {"resp_code": "200", "result": {}}}) == []
    cases = [
        ({"error_response": {"code": "InvalidAppKey", "msg": "x"}}, "identifiants"),
        ({"error_response": {"code": "IncompleteSignature"}}, "identifiants"),
        ({"error_response": {"code": "InsufficientPermission"}}, "refusé"),
        ({"error_response": {"code": "ApiCallLimit"}}, "Quota"),
        ({"resp_result": {"resp_code": "405", "resp_msg": "bad"}}, "405"),
    ]
    for body, message in cases:
        with pytest.raises(ConnectorError, match=message):
            products_from(body)


class FakeAliExpress:
    def __init__(self, body=None, status=200):
        self.body = (
            envelope([PRODUCT, {**PRODUCT, "product_id": "2", "target_sale_price": "9"}])
            if body is None
            else body
        )
        self.status = status
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(self.status, json=self.body)

    def connector(self, settings: Settings = CONFIGURED) -> AliExpressConnector:
        return AliExpressConnector(settings, transport=httpx.MockTransport(self))


def test_search_against_simulated_gateway():
    fake = FakeAliExpress()
    c = fake.connector()
    offers = run_bounded(c.search(SearchQuery(keywords="coque", max_price=Decimal("5"))))
    assert [o.external_id for o in offers] == ["1005001"]  # 9 € filtré localement
    assert c.api_calls == 1
    req = fake.requests[0]
    assert req.url.host == "api-sg.aliexpress.com" and req.url.path == "/sync"
    query = parse_qs(req.url.query.decode())
    assert query["method"] == [METHOD] and query["keywords"] == ["coque"]
    assert "max_sale_price" not in query  # unité ambiguë : jamais envoyée


def test_http_errors_are_explicit():
    with pytest.raises(ConnectorError, match="HTTP 500"):
        run_bounded(FakeAliExpress(status=500).connector().search(SearchQuery(keywords="x")))


def use_fake(monkeypatch, fake):
    monkeypatch.setattr(
        connector_service, "get_connector", lambda slug, settings: fake.connector(settings)
    )


def test_real_test_flow_and_collection(db: Session, monkeypatch):
    use_fake(monkeypatch, FakeAliExpress())
    result = connector_service.test_source(db, "aliexpress", "test", CONFIGURED)
    assert result.ok and result.status == "active" and result.api_calls == 1
    run = connector_service.collect_from_source(
        db, "aliexpress", SearchQuery(keywords="coque"), "test", CONFIGURED
    )
    assert run.offers_created == 2
    offer = db.scalars(select(Offer).where(Offer.external_id == "1005001")).one()
    assert offer.price_eur == Decimal("1.89") and offer.shipping_amount is None
    assert offer.merchant is not None and offer.merchant.name == "Case Factory Store"


@pytest.mark.parametrize(
    ("fake", "settings", "status"),
    [
        (
            FakeAliExpress({"error_response": {"code": "InvalidAppKey"}}),
            CONFIGURED,
            SourceStatus.needs_credentials,
        ),
        (
            FakeAliExpress({"error_response": {"code": "InsufficientPermission"}}),
            CONFIGURED,
            SourceStatus.needs_approval,
        ),
        (FakeAliExpress(), Settings(), SourceStatus.needs_credentials),
    ],
)
def test_failed_tests_never_activate(db: Session, monkeypatch, fake, settings, status):
    use_fake(monkeypatch, fake)
    result = connector_service.test_source(db, "aliexpress", "test", settings)
    assert result.ok is False and result.status == status.value
    source = db.scalars(select(Source).where(Source.slug == "aliexpress")).one()
    assert source.status == status
