"""Registre des connecteurs implémentés. Une source sans connecteur ici ne peut pas collecter."""

from dataclasses import dataclass

from app.connectors.aliexpress import ALIEXPRESS_SLUG, AliExpressConnector
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
    ALIEXPRESS_SLUG: ConnectorInfo(
        slug=ALIEXPRESS_SLUG,
        name="AliExpress (API d'affiliation officielle)",
        family="marketplace",
        homepage_url="https://fr.aliexpress.com",
        description="Produits livrables en France, prix en euros. Gratuit ; nécessite le "
        "programme d'affiliation et une application Open Platform. Frais de port non fournis.",
    ),
}


def get_connector(slug: str, settings: Settings) -> SourceConnector | None:
    if slug == DEMO_SLUG:
        return DemoConnector()
    if slug == EBAY_SLUG:
        return EbayConnector(settings)
    if slug == ALIEXPRESS_SLUG:
        return AliExpressConnector(settings)
    return None


def implemented_slugs() -> list[str]:
    return list(CONNECTORS)


def is_configured(slug: str, settings: Settings) -> bool:
    if slug == EBAY_SLUG:
        return settings.ebay_configured
    if slug == ALIEXPRESS_SLUG:
        return settings.aliexpress_configured
    return True


def daily_call_budget(slug: str, settings: Settings) -> int | None:
    if slug == EBAY_SLUG:
        return settings.ebay_daily_call_budget
    if slug == ALIEXPRESS_SLUG:
        return settings.aliexpress_daily_call_budget
    return None


def max_calls_per_run(slug: str, settings: Settings) -> int:
    """Appels API maximum d'une collecte, réservés sur le quota avant de la lancer."""
    if slug == EBAY_SLUG:
        return 2  # jeton + recherche
    if slug == ALIEXPRESS_SLUG:
        return 1 + settings.aliexpress_shipping_lookups_per_run
    return 0
