"""Registre des connecteurs implémentés. Une source sans connecteur ici ne peut pas collecter."""

from dataclasses import dataclass

from app.connectors.base import SourceConnector
from app.connectors.demo import DEMO_SLUG, DemoConnector
from app.connectors.ebay import EBAY_SLUG, EbayConnector
from app.core.config import Settings


@dataclass(frozen=True)
class ConnectorInfo:
    slug: str
    name: str
    family: str
    homepage_url: str | None
    description: str


CONNECTORS: dict[str, ConnectorInfo] = {
    DEMO_SLUG: ConnectorInfo(
        slug=DEMO_SLUG,
        name="Source DEMO (données fictives)",
        family="demo",
        homepage_url=None,
        description="Offres inventées pour essayer l'application. Aucun accès externe.",
    ),
    EBAY_SLUG: ConnectorInfo(
        slug=EBAY_SLUG,
        name="eBay (Browse API officielle)",
        family="marketplace",
        homepage_url="https://www.ebay.fr",
        description="Annonces à prix fixe livrables en France, triées des plus récentes aux plus "
        "anciennes. Gratuit, 5 000 appels/jour par défaut. Nécessite un compte développeur eBay.",
    ),
}


def get_connector(slug: str, settings: Settings) -> SourceConnector | None:
    if slug == DEMO_SLUG:
        return DemoConnector()
    if slug == EBAY_SLUG:
        return EbayConnector(settings)
    return None


def implemented_slugs() -> list[str]:
    return list(CONNECTORS)


def is_configured(slug: str, settings: Settings) -> bool:
    if slug == EBAY_SLUG:
        return settings.ebay_configured
    return True


def daily_call_budget(slug: str, settings: Settings) -> int | None:
    if slug == EBAY_SLUG:
        return settings.ebay_daily_call_budget
    return None
