"""API : données DEMO, offres, historique de prix, exécutions de connecteurs."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models import AuditLog


def load(client) -> dict:
    res = client.post("/api/v1/demo/load")
    assert res.status_code == 200, res.text
    return res.json()


def test_demo_load_and_offers_listing(client):
    run = load(client)
    assert run["status"] == "success" and run["is_demo"] is True
    page = client.get("/api/v1/offers").json()
    assert page["total"] == 6 and len(page["items"]) == 6
    item = page["items"][0]
    assert item["is_demo"] and item["source"]["slug"] == "demo"
    assert {"last_verified_at", "is_stale", "access_method", "match_method"} <= item.keys()
    assert item["is_stale"] is False


def test_offer_filters_sort_and_pagination(client):
    load(client)
    get = lambda **p: client.get("/api/v1/offers", params=p).json()  # noqa: E731
    assert get(q="veste")["total"] == 2
    assert get(q="%")["total"] == 0  # jokers SQL neutralisés
    assert get(brand="beta demo")["total"] == 2
    assert get(availability="out_of_stock")["total"] == 1
    # Filtre prix EUR : les offres sans prix EUR connu sont exclues, jamais comptées à 0.
    cheap = get(max_price_eur="60")["items"]
    assert {o["currency"] for o in cheap} == {"EUR"} and len(cheap) == 2
    ordered = get(sort="price_eur_asc")["items"]
    assert [o["price_eur"] for o in ordered][-2:] == [None, None]
    page1, page2 = get(limit=4, offset=0), get(limit=4, offset=4)
    assert len(page1["items"]) == 4 and len(page2["items"]) == 2
    ids = {o["id"] for o in page1["items"]} | {o["id"] for o in page2["items"]}
    assert len(ids) == 6
    assert client.get("/api/v1/offers", params={"limit": 0}).status_code == 422


def test_price_with_shipping_only_when_both_known(client):
    load(client)
    items = {o["title"]: o for o in client.get("/api/v1/offers").json()["items"]}
    assert items["[DEMO] Basket DEMO Alpha A1"]["price_with_shipping_eur"] == "64.80"
    assert items["[DEMO] Basket DEMO Alpha A1 (noir)"]["price_with_shipping_eur"] is None
    assert items["[DEMO] Polo DEMO Gamma G2"]["price_eur"] is None


def test_offer_detail_and_price_history(client):
    load(client)
    offers = client.get("/api/v1/offers", params={"q": "Alpha A1"}).json()["items"]
    detail = client.get(f"/api/v1/offers/{offers[0]['id']}").json()
    assert len(detail["observations"]) == 1
    history = client.get(f"/api/v1/products/{detail['product_id']}/price-history").json()
    assert history["offers_count"] == 2 and len(history["points"]) == 2
    assert history["is_demo"] is True
    missing = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"/api/v1/offers/{missing}").status_code == 404
    assert client.get(f"/api/v1/products/{missing}/price-history").status_code == 404
    assert client.get("/api/v1/offers/pas-un-uuid").status_code == 422


def test_dashboard_and_status_reflect_collection(client):
    assert client.get("/api/v1/dashboard/summary").json()["last_refresh_at"] is None
    load(client)
    summary = client.get("/api/v1/dashboard/summary").json()
    assert summary["data_mode"] == "demo"
    assert summary["offers_total"] == 6
    assert summary["last_refresh_at"] is not None and summary["is_stale"] is False
    runs = client.get("/api/v1/connector-runs").json()
    assert len(runs) == 1 and runs[0]["offers_created"] == 6
    components = client.get("/api/v1/system/status").json()["components"]
    connectors = next(c for c in components if c["name"] == "Connecteurs de données")
    assert connectors["status"] == "not_configured" and "DEMO" in connectors["detail"]


def test_demo_purge_removes_everything_and_is_audited(client, db: Session):
    load(client)
    res = client.delete("/api/v1/demo")
    assert res.json() == {
        "offers_deleted": 6,
        "products_deleted": 4,
        "merchants_deleted": 5,
        "sources_deleted": 1,
    }
    assert client.get("/api/v1/offers").json()["total"] == 0
    assert client.get("/api/v1/dashboard/summary").json()["data_mode"] == "empty"
    actions = {a.action for a in db.scalars(select(AuditLog)).all()}
    assert {"collection.run", "demo.purge"} <= actions
    # Rechargement possible après suppression.
    assert load(client)["offers_created"] == 6


def test_demo_routes_require_token_when_configured(client):
    from app.main import app

    app.dependency_overrides[get_settings] = lambda: Settings(api_access_token="s3cret-test")
    try:
        assert client.post("/api/v1/demo/load").status_code == 401
        assert client.delete("/api/v1/demo").status_code == 401
        ok = client.post("/api/v1/demo/load", headers={"Authorization": "Bearer s3cret-test"})
        assert ok.status_code == 200
    finally:
        app.dependency_overrides.pop(get_settings, None)
