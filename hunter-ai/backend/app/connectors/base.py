"""Contrat commun à tous les connecteurs de sources (cahier des charges §4.2).

Un connecteur ne fait que *lire* une source autorisée et renvoyer des offres brutes. Il ne touche
jamais à la base de données : la normalisation, la déduplication et l'enregistrement sont faits
par `app.services.collection_service`, identiques pour toutes les sources.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Protocol, runtime_checkable

from app.models.source import AccessMethod


class ConnectorError(Exception):
    """Erreur d'un connecteur (source indisponible, quota atteint, réponse invalide…)."""


@dataclass(frozen=True)
class SearchQuery:
    keywords: str = ""
    brand: str | None = None
    gtin: str | None = None
    max_price: Decimal | None = None
    limit: int = 50


@dataclass(frozen=True)
class SourceHealth:
    ok: bool
    detail: str


@dataclass(frozen=True)
class SourceCapabilities:
    access_method: AccessMethod
    supports_search: bool
    supports_fetch_offer: bool
    supports_gtin_search: bool
    max_results_per_query: int
    # Délai minimal entre deux appels, en secondes (respect des quotas de la source).
    min_interval_seconds: float
    is_demo: bool
    limits: str = ""


@dataclass(frozen=True)
class RawOffer:
    """Offre telle que fournie par la source, avant normalisation. Champs inconnus = None."""

    external_id: str
    title: str
    url: str
    price: Decimal
    currency: str
    observed_at: datetime
    availability: str = "unknown"
    condition: str = "unknown"
    shipping_cost: Decimal | None = None
    merchant_name: str | None = None
    merchant_country: str | None = None
    country: str | None = None
    brand: str | None = None
    model: str | None = None
    mpn: str | None = None
    gtin: str | None = None
    category: str | None = None
    size: str | None = None
    color: str | None = None
    extra: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class SourceConnector(Protocol):
    source_slug: str

    async def health_check(self) -> SourceHealth: ...

    async def get_capabilities(self) -> SourceCapabilities: ...

    async def search(self, query: SearchQuery) -> list[RawOffer]: ...

    async def fetch_offer(self, external_id: str) -> RawOffer | None: ...
