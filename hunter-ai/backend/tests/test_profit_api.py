"""API du calculateur de rentabilité et des ventes réalisées."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models import AuditLog


def sale(client, **over):
    body = {
        "title": "Polo Ralph Lauren M",
        "brand": "Ralph Lauren",
        "channel": "vinted",
        "sale_price": "30",
        "sold_on": "2026-11-01",
    }
    body.update(over)
    res = client.post("/api/v1/resale-records", json=body)
    assert res.status_code == 201, res.text
    return res.json()


def test_calculate_endpoint(client):
    res = client.post(
        "/api/v1/profit/calculate",
        json={
            "unit_price": "1.50",
            "quantity": 20,
            "shipping_cost": "12",
            "origin": "non_eu",
            "article_categories": 1,
            "vat_status": "unknown",
            "resale_central": "9",
            "resale_low": "7",
            "resale_high": "12",
            "selling_fee_pct": "5",
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    keys = [line["key"] for line in body["lines"]]
    assert keys[:5] == ["purchase", "shipping", "customs_duty", "processing_fee", "import_vat"]
    vat = next(line for line in body["lines"] if line["key"] == "import_vat")
    assert vat["status"] == "range"
    assert body["landed_cost"]["low"] == "47.00"  # 30 + 12 + 3 + 2
    assert len(body["scenarios"]) == 3 and body["rules_version"] == "2026-11-24"
    assert any("validation douanière" in w for w in body["warnings"])


def test_calculate_validation(client):
    bad = [
        {"unit_price": "-1"},
        {"unit_price": "1", "defect_rate_pct": "150"},
        {"unit_price": "1", "quantity": 0},
        {"unit_price": "1", "origin": "mars"},
        {"unit_price": "1", "hack": True},
    ]
    for body in bad:
        assert client.post("/api/v1/profit/calculate", json=body).status_code == 422, body


def test_resale_records_crud_audit_and_real_profit(client, db: Session):
    full = sale(client, platform_fees="1.50", shipping_paid="0", purchase_cost="8")
    partial = sale(client, sale_price="25")
    assert full["real_profit"] == "20.50"  # 30 − 1,50 − 0 − 8
    assert partial["real_profit"] is None  # coûts non renseignés : pas de bénéfice inventé
    page = client.get("/api/v1/resale-records").json()
    assert page["total"] == 2
    assert client.delete(f"/api/v1/resale-records/{partial['id']}").status_code == 204
    assert client.get("/api/v1/resale-records").json()["total"] == 1
    missing = "00000000-0000-0000-0000-000000000000"
    assert client.delete(f"/api/v1/resale-records/{missing}").status_code == 404
    actions = [a.action for a in db.scalars(select(AuditLog)).all()]
    assert actions.count("resale.create") == 2 and "resale.delete" in actions


def test_reference_from_real_sales(client):
    empty = client.get("/api/v1/resale-records/reference", params={"brand": "lacoste"}).json()
    assert empty["count"] == 0 and empty["enough"] is False and empty["median"] is None
    for price in ("20", "24", "30", "36", "40"):
        sale(client, sale_price=price)
    sale(client, brand="Lacoste", title="Polo Lacoste", sale_price="99")
    ref = client.get("/api/v1/resale-records/reference", params={"brand": "ralph lauren"}).json()
    assert ref["count"] == 5 and ref["enough"] is True
    assert (ref["minimum"], ref["low"], ref["median"], ref["high"], ref["maximum"]) == (
        "20.00",
        "24.00",
        "30.00",
        "36.00",
        "40.00",
    )
    two = client.get("/api/v1/resale-records/reference", params={"q": "lacoste"}).json()
    assert two["count"] == 1 and two["enough"] is False


def test_resale_validation_and_token(client):
    assert client.post("/api/v1/resale-records", json={"title": "x"}).status_code == 422
    assert (
        client.post(
            "/api/v1/resale-records",
            json={"title": "x", "sale_price": "5", "sold_on": "2026-11-01", "channel": "amazon"},
        ).status_code
        == 422
    )
    from app.main import app

    app.dependency_overrides[get_settings] = lambda: Settings(api_access_token="s3cret-test")
    try:
        res = client.post(
            "/api/v1/resale-records",
            json={"title": "x", "sale_price": "5", "sold_on": "2026-11-01"},
        )
        assert res.status_code == 401
        # Le calcul ne modifie rien : il reste accessible sans jeton.
        assert client.post("/api/v1/profit/calculate", json={"unit_price": "1"}).status_code == 200
    finally:
        app.dependency_overrides.pop(get_settings, None)
