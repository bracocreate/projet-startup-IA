from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models import AuditLog, Source, SourceStatus, UserSettings
from app.services.settings_service import get_or_create_settings


def test_health_ok(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["database"] == "ok"
    assert "x-request-id" in r.headers


def test_system_status_reports_migrations_and_unimplemented_parts(client):
    body = client.get("/api/v1/system/status").json()
    names = {c["name"]: c["status"] for c in body["components"]}
    assert names["Base de données"] == "ok"
    assert names["Migrations"] == "ok"
    assert body["db_revision"] == body["db_revision_expected"]
    # On n'annonce jamais comme actif ce qui n'existe pas encore.
    assert (
        names["Connecteurs de données"] == "not_configured"
    )  # DEMO seulement, aucune source réelle
    assert names["Planificateur"] == "not_implemented"


def test_dashboard_empty_state_is_explicit(client):
    body = client.get("/api/v1/dashboard/summary").json()
    assert body["data_mode"] == "empty"
    assert body["last_refresh_at"] is None
    assert body["is_stale"] is True
    assert body["sources_total"] == 0
    assert [s["key"] for s in body["rankings"]] == ["best_deals", "emerging_trends", "new_markets"]
    assert all(s["items"] == [] for s in body["rankings"])


def test_dashboard_flags_demo_and_error_sources(client, db: Session):
    db.add_all(
        [
            Source(slug="demo", name="Source DEMO", family="demo", is_demo=True),
            Source(slug="broken", name="Cassée", family="api", status=SourceStatus.error),
        ]
    )
    db.commit()
    body = client.get("/api/v1/dashboard/summary").json()
    assert body["data_mode"] == "demo"
    assert body["sources_total"] == 2
    assert [s["slug"] for s in body["sources_in_error"]] == ["broken"]
    assert [s["slug"] for s in client.get("/api/v1/sources").json()] == ["broken", "demo"]


def test_settings_defaults_match_spec(client):
    s = client.get("/api/v1/settings").json()
    assert s["currency"] == "EUR"
    assert s["timezone"] == "Europe/Paris"
    assert s["max_item_budget_eur"] == "100.00"
    assert s["max_lot_budget_eur"] is None
    assert s["daily_collection_start"] == "06:00:00"
    assert s["daily_collection_duration_min"] == 120
    assert "Nike" in s["priority_brands"]
    assert s["auto_purchase_allowed"] is False


def test_settings_patch_is_validated_and_audited(client, db: Session):
    r = client.patch(
        "/api/v1/settings",
        json={"max_item_budget_eur": "150", "priority_brands": [" Nike ", "Nike", "Puma"]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["max_item_budget_eur"] == "150.00"
    assert r.json()["priority_brands"] == ["Nike", "Puma"]
    logs = db.scalars(select(AuditLog)).all()
    assert len(logs) == 1 and logs[0].action == "settings.update" and logs[0].actor == "local"
    assert "max_item_budget_eur" in logs[0].details["changes"]


def test_settings_patch_without_change_writes_no_audit(client, db: Session):
    client.get("/api/v1/settings")
    client.patch("/api/v1/settings", json={"timezone": "Europe/Paris"})
    assert db.scalars(select(AuditLog)).all() == []


def test_settings_patch_rejects_invalid_input(client):
    assert client.patch("/api/v1/settings", json={"timezone": "Mars/Olympus"}).status_code == 422
    assert client.patch("/api/v1/settings", json={"max_item_budget_eur": -1}).status_code == 422
    # Champ non modifiable : l'achat automatique ne peut pas être activé via l'API.
    r = client.patch("/api/v1/settings", json={"auto_purchase_allowed": True})
    assert r.status_code == 422


def test_auto_purchase_blocked_at_database_level(db: Session):
    s: UserSettings = get_or_create_settings(db)
    s.auto_purchase_allowed = True
    try:
        db.commit()
        raise AssertionError("La contrainte aurait dû refuser l'écriture")
    except IntegrityError:
        db.rollback()


def test_patch_requires_token_when_configured(client):
    from app.main import app

    app.dependency_overrides[get_settings] = lambda: Settings(api_access_token="s3cret-test")
    try:
        assert client.patch("/api/v1/settings", json={}).status_code == 401
        r = client.patch(
            "/api/v1/settings", json={}, headers={"Authorization": "Bearer s3cret-test"}
        )
        assert r.status_code == 200
    finally:
        app.dependency_overrides.pop(get_settings)


def test_patch_refused_in_production_without_token(client):
    from app.main import app

    app.dependency_overrides[get_settings] = lambda: Settings(app_env="production")
    try:
        assert client.patch("/api/v1/settings", json={}).status_code == 403
    finally:
        app.dependency_overrides.pop(get_settings)


def test_openapi_available(client):
    paths = client.get("/api/openapi.json").json()["paths"]
    for p in ["/api/v1/health", "/api/v1/dashboard/summary", "/api/v1/settings"]:
        assert p in paths
