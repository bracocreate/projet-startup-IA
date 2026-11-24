"""Tests des services de santé : cas d'erreur non couverts par les tests d'API nominaux."""

from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.services import system_service


def test_health_returns_503_when_database_unreachable() -> None:
    from app.db.session import get_db
    from app.main import app

    # Port fermé : la connexion échoue immédiatement, sans toucher à une vraie base.
    dead = create_engine("postgresql+psycopg://nobody:x@127.0.0.1:1/none?connect_timeout=1")

    def broken_db() -> Iterator[Session]:
        with Session(dead) as session:
            yield session

    app.dependency_overrides[get_db] = broken_db
    try:
        with TestClient(app) as c:
            res = c.get("/api/v1/health")
            status_body = c.get("/api/v1/system/status").json()
    finally:
        app.dependency_overrides.clear()
        dead.dispose()

    assert res.status_code == 503
    assert res.json()["database"] == "error"
    assert status_body["components"][0] == {
        "name": "Base de données",
        "status": "error",
        "detail": "PostgreSQL injoignable",
    }


def test_system_status_warns_when_migrations_are_behind(db: Session) -> None:
    db.execute(text("UPDATE alembic_version SET version_num = '0000'"))
    try:
        result = system_service.build_system_status(db, Settings())
    finally:
        db.rollback()

    migrations = next(c for c in result.components if c.name == "Migrations")
    assert migrations.status == "warning"
    assert "0000" in migrations.detail
    assert result.db_revision == "0000"
