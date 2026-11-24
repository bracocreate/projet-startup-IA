"""Connecteur de DÉMONSTRATION. Toutes ses données sont fictives et marquées DEMO.

- Marques et produits inventés (aucune marque réelle, pour ne jamais associer un faux prix à un
  vrai produit) ; codes GTIN de la plage GS1 « 2xx » (usage interne, jamais attribuée à un
  produit du commerce) ; liens vers `example.com`, domaine réservé (RFC 2606).
- Sert à tester la chaîne complète (normalisation, déduplication, historique) sans aucun accès
  externe. `revision` permet de simuler une évolution de prix entre deux collectes.
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import NamedTuple

from app.connectors.base import (
    ConnectorError,
    RawOffer,
    SearchQuery,
    SourceCapabilities,
    SourceHealth,
)
from app.models.source import AccessMethod

DEMO_SLUG = "demo"
DEMO_URL = "https://example.com/demo/offre/"


class DemoItem(NamedTuple):
    external_id: str
    title: str
    brand: str
    mpn: str | None
    gtin: str | None
    price: str
    currency: str
    shipping: str | None  # None = frais inconnus ; "0" = livraison gratuite
    merchant: str
    country: str
    availability: str
    size: str | None


_CATALOG: list[DemoItem] = [
    DemoItem(
        "D-001",
        "Basket DEMO Alpha A1",
        "Alpha DEMO",
        "A1-BLK",
        "2000000000015",
        "59.90",
        "EUR",
        "4.90",
        "Boutique DEMO Paris",
        "FR",
        "in_stock",
        "42",
    ),
    DemoItem(
        "D-002",
        "Basket DEMO Alpha A1 (noir)",
        "Alpha DEMO",
        "A1-BLK",
        "2000000000015",
        "54.00",
        "EUR",
        None,
        "Outlet DEMO Lyon",
        "FR",
        "in_stock",
        "42",
    ),
    DemoItem(
        "D-003",
        "Veste DEMO Beta B7",
        "Beta DEMO",
        "B7-NVY",
        None,
        "89.00",
        "EUR",
        "0",
        "Boutique DEMO Paris",
        "FR",
        "in_stock",
        "M",
    ),
    DemoItem(
        "D-004",
        "Veste DEMO Beta B7 navy",
        "beta demo",
        "b7-nvy",
        None,
        "79.00",
        "EUR",
        "6.50",
        "Déstockage DEMO Lille",
        "FR",
        "out_of_stock",
        "M",
    ),
    DemoItem(
        "D-005",
        "Polo DEMO Gamma G2",
        "Gamma DEMO",
        None,
        None,
        "35.00",
        "USD",
        "12.00",
        "Store DEMO New York",
        "US",
        "in_stock",
        "L",
    ),
    DemoItem(
        "D-006",
        "Sac DEMO Delta D9",
        "Delta DEMO",
        "D9",
        "2000000000022",
        "45.00",
        "GBP",
        None,
        "Shop DEMO London",
        "GB",
        "unknown",
        None,
    ),
]


class DemoConnector:
    source_slug = DEMO_SLUG

    def __init__(self, revision: int = 1, fail: bool = False) -> None:
        self.revision = revision
        self.fail = fail

    async def health_check(self) -> SourceHealth:
        if self.fail:
            return SourceHealth(ok=False, detail="Panne simulée (DEMO).")
        return SourceHealth(ok=True, detail="Connecteur DEMO : données fictives locales.")

    async def get_capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            access_method=AccessMethod.manual_import,
            supports_search=True,
            supports_fetch_offer=True,
            supports_gtin_search=True,
            max_results_per_query=50,
            min_interval_seconds=0,
            is_demo=True,
            limits="Jeu de données fictif fixe ; aucun accès réseau.",
        )

    def _offers(self) -> list[RawOffer]:
        now = datetime.now(UTC)
        offers = []
        for item in _CATALOG:
            amount = Decimal(item.price)
            # Révision 2 : baisse de prix simulée sur D-001.
            if self.revision >= 2 and item.external_id == "D-001":
                amount = Decimal("49.90")
            offers.append(
                RawOffer(
                    external_id=item.external_id,
                    title=f"[DEMO] {item.title}",
                    url=f"{DEMO_URL}{item.external_id}",
                    price=amount,
                    currency=item.currency,
                    observed_at=now,
                    availability=item.availability,
                    condition="new",
                    shipping_cost=Decimal(item.shipping) if item.shipping is not None else None,
                    merchant_name=item.merchant,
                    merchant_country=item.country,
                    country=item.country,
                    brand=item.brand,
                    mpn=item.mpn,
                    gtin=item.gtin,
                    category="Mode (DEMO)",
                    size=item.size,
                )
            )
        return offers

    async def search(self, query: SearchQuery) -> list[RawOffer]:
        if self.fail:
            raise ConnectorError("Panne simulée du connecteur DEMO.")
        words = query.keywords.casefold().split()
        result = [
            o
            for o in self._offers()
            if all(w in o.title.casefold() for w in words)
            and (query.brand is None or (o.brand or "").casefold() == query.brand.casefold())
            and (query.gtin is None or o.gtin == query.gtin)
            and (query.max_price is None or o.price <= query.max_price)
        ]
        return result[: query.limit]

    async def fetch_offer(self, external_id: str) -> RawOffer | None:
        return next((o for o in self._offers() if o.external_id == external_id), None)
