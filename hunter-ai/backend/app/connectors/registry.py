"""Registre des connecteurs implémentés. Une source sans connecteur ici ne peut pas collecter."""

from app.connectors.base import SourceConnector
from app.connectors.demo import DEMO_SLUG, DemoConnector


def get_connector(slug: str) -> SourceConnector | None:
    if slug == DEMO_SLUG:
        return DemoConnector()
    return None


def implemented_slugs() -> list[str]:
    return [DEMO_SLUG]
