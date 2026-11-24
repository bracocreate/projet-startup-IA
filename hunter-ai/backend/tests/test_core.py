import json
import logging

from sqlalchemy import create_engine, inspect, text

from alembic import command
from app.core.config import Settings
from app.core.logging import JsonFormatter, redact, redact_mapping
from tests.conftest import alembic_config


def test_database_url_built_from_parts():
    s = Settings(postgres_user="u", postgres_password="p@ss", postgres_host="db", postgres_db="x")
    assert s.database_url == "postgresql+psycopg://u:p%40ss@db:5432/x"
    assert "p@ss" not in repr(s)  # SecretStr masqué


def test_cors_origins_parsed():
    s = Settings(cors_origins="http://a.local, http://b.local,")
    assert s.cors_origin_list == ["http://a.local", "http://b.local"]


def test_redaction_of_secrets():
    assert redact("postgresql://user:topsecret@db/x") == "postgresql://user:***@db/x"
    assert redact("token=abc123 ok") == "token=*** ok"
    assert redact_mapping({"api_key": "k", "nested": {"password": "p"}, "n": 1}) == {
        "api_key": "***",
        "nested": {"password": "***"},
        "n": 1,
    }


def test_json_log_line_has_no_secret():
    rec = logging.makeLogRecord(
        {"msg": "connexion postgresql://u:pw@h/db", "levelname": "INFO", "token": "zzz"}
    )
    line = json.loads(JsonFormatter().format(rec))
    assert "pw" not in line["msg"] and line["token"] == "***"


def test_migrations_downgrade_and_upgrade_roundtrip(db_url, engine):
    cfg = alembic_config(db_url)
    command.downgrade(cfg, "base")
    insp = inspect(create_engine(db_url))
    assert "sources" not in insp.get_table_names()
    with engine.connect() as conn:
        enums = conn.execute(text("SELECT typname FROM pg_type WHERE typname='source_status'"))
        assert enums.first() is None
    command.upgrade(cfg, "head")
    insp = inspect(create_engine(db_url))
    assert {"users", "user_settings", "sources", "audit_logs"} <= set(insp.get_table_names())
