"""Connecteur eBay Browse API (accès officiel, lecture seule).

Documentation vérifiée le 24/11/2026 sur developer.ebay.com :
- Jeton : POST {base}/identity/v1/oauth2/token, « client credentials », en-tête
  Authorization: Basic base64(client_id:client_secret), portée https://api.ebay.com/oauth/api_scope,
  durée de vie 7 200 s.
- Recherche : GET {base}/buy/browse/v1/item_summary/search — q, gtin, filter, sort=newlyListed
  (tri par date de mise en vente), limit 1–200, 10 000 résultats max ; en-tête
  X-EBAY-C-MARKETPLACE-ID (EBAY_US par défaut si absent).
- Quota par défaut : 5 000 appels/jour. Les « Buy APIs » peuvent exiger une approbation eBay
  Partner Network en production : un refus (401/403) est donc signalé comme tel, jamais contourné.

Choix prudents : uniquement les annonces à prix fixe (le prix d'une enchère n'est pas final),
livrables en France ; frais de livraison retenus seulement s'ils sont fixes et dans la devise du
prix (sinon « inconnus »). Les informations vendeur ne sont pas enregistrées en base.
"""

import base64
import time
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from threading import Lock
from typing import Any

import httpx

from app.connectors.base import (
    ConnectorError,
    RawOffer,
    SearchQuery,
    SourceCapabilities,
    SourceHealth,
)
from app.core.config import Settings
from app.models.source import AccessMethod

EBAY_SLUG = "ebay"
SCOPE = "https://api.ebay.com/oauth/api_scope"
BASE_URLS = {
    "production": "https://api.ebay.com",
    "sandbox": "https://api.sandbox.ebay.com",
}
MAX_LIMIT = 200
TIMEOUT = httpx.Timeout(20.0)
TOKEN_SAFETY_MARGIN_S = 120

# Jetons partagés entre instances du connecteur (évite un appel « jeton » à chaque collecte).
_token_cache: dict[tuple[str, str], tuple[str, float]] = {}
_token_lock = Lock()


def condition_from_id(condition_id: str | None) -> str:
    """Correspondance prudente des codes d'état eBay ; dans le doute : « unknown »."""
    try:
        code = int(condition_id or "")
    except ValueError:
        return "unknown"
    if code == 1000:
        return "new"
    if 2000 <= code <= 2500:
        return "refurbished"
    if 2750 <= code <= 6000:
        return "used"
    return "unknown"  # 1500/1750 (neuf autre / avec défauts), 7000 (pour pièces)…


def decimal_or_none(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value)) if value is not None else None
    except InvalidOperation:
        return None


def fixed_shipping(item: dict[str, Any], currency: str) -> Decimal | None:
    for option in item.get("shippingOptions") or []:
        cost = option.get("shippingCost") or {}
        if option.get("shippingCostType") == "FIXED" and cost.get("currency") == currency:
            return decimal_or_none(cost.get("value"))
    return None


def to_raw_offer(item: dict[str, Any], observed_at: datetime) -> RawOffer | None:
    price = item.get("price") or {}
    amount = decimal_or_none(price.get("value"))
    currency = price.get("currency")
    if not item.get("itemId") or amount is None or not currency or not item.get("itemWebUrl"):
        return None
    location = item.get("itemLocation") or {}
    return RawOffer(
        external_id=str(item["itemId"]),
        title=str(item.get("title") or ""),
        # Lien public de l'annonce (pas le lien d'affiliation).
        url=str(item["itemWebUrl"]),
        price=amount,
        currency=str(currency),
        observed_at=observed_at,
        # La recherche ne renvoie que des annonces actives ; la quantité restante n'est pas
        # fournie : disponibilité « à confirmer » plutôt que « en stock ».
        availability="unknown",
        condition=condition_from_id(item.get("conditionId")),
        shipping_cost=fixed_shipping(item, str(currency)),
        merchant_name=None,  # vendeur eBay : non enregistré (données de particuliers possibles)
        country=location.get("country"),
        category=((item.get("categories") or [{}])[0]).get("categoryName"),
    )


def ebay_error_message(response: httpx.Response) -> str:
    try:
        errors = response.json().get("errors") or []
        first = errors[0] if errors else {}
        return str(first.get("longMessage") or first.get("message") or "")[:300]
    except (ValueError, AttributeError):
        return ""


class EbayConnector:
    source_slug = EBAY_SLUG

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.base_url = BASE_URLS[settings.ebay_environment]
        self.transport = transport
        self.api_calls = 0

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.base_url, timeout=TIMEOUT, transport=self.transport)

    async def token(self) -> str:
        key = (self.settings.ebay_environment, self.settings.ebay_client_id)
        with _token_lock:
            cached = _token_cache.get(key)
        if cached and cached[1] > time.monotonic():
            return cached[0]
        if not self.settings.ebay_configured:
            raise ConnectorError("Identifiants eBay absents : renseignez EBAY_CLIENT_ID/SECRET.")
        raw = (
            f"{self.settings.ebay_client_id}:{self.settings.ebay_client_secret.get_secret_value()}"
        )
        async with self.client() as client:
            self.api_calls += 1
            try:
                response = await client.post(
                    "/identity/v1/oauth2/token",
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Authorization": "Basic " + base64.b64encode(raw.encode()).decode(),
                    },
                    data={"grant_type": "client_credentials", "scope": SCOPE},
                )
            except httpx.HTTPError as exc:
                raise ConnectorError(f"eBay injoignable ({type(exc).__name__}).") from exc
        if response.status_code in (400, 401):
            raise ConnectorError("eBay refuse les identifiants (vérifiez App ID et Cert ID).")
        if response.status_code != 200:
            raise ConnectorError(f"Jeton eBay refusé (HTTP {response.status_code}).")
        body = response.json()
        token = str(body["access_token"])
        expires_in = int(body.get("expires_in", 7200))
        with _token_lock:
            _token_cache[key] = (token, time.monotonic() + expires_in - TOKEN_SAFETY_MARGIN_S)
        return token

    async def health_check(self) -> SourceHealth:
        if not self.settings.ebay_configured:
            return SourceHealth(ok=False, detail="Identifiants eBay non configurés dans .env.")
        try:
            await self.token()
        except ConnectorError as exc:
            return SourceHealth(ok=False, detail=str(exc))
        return SourceHealth(ok=True, detail="Jeton eBay obtenu.")

    async def get_capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            access_method=AccessMethod.official_api,
            supports_search=True,
            supports_fetch_offer=False,
            supports_gtin_search=True,
            max_results_per_query=MAX_LIMIT,
            min_interval_seconds=1,
            is_demo=False,
            limits="5 000 appels/jour par défaut ; 10 000 résultats max par recherche ; "
            "Buy APIs : approbation eBay Partner Network possible en production.",
        )

    def search_params(self, query: SearchQuery) -> dict[str, str]:
        filters = ["buyingOptions:{FIXED_PRICE}", "deliveryCountry:FR"]
        if query.max_price is not None:
            filters.append(f"price:[..{query.max_price}]")
            filters.append("priceCurrency:EUR")
        params = {
            "sort": "newlyListed",
            "limit": str(max(1, min(query.limit, MAX_LIMIT))),
            "filter": ",".join(filters),
        }
        keywords = " ".join(filter(None, [query.brand, query.keywords])).strip()
        if keywords:
            params["q"] = keywords[:100]
        if query.gtin:
            params["gtin"] = query.gtin
        if "q" not in params and "gtin" not in params:
            raise ConnectorError("Recherche eBay : indiquez des mots-clés, une marque ou un GTIN.")
        return params

    async def search(self, query: SearchQuery) -> list[RawOffer]:
        params = self.search_params(query)
        token = await self.token()
        async with self.client() as client:
            self.api_calls += 1
            try:
                response = await client.get(
                    "/buy/browse/v1/item_summary/search",
                    params=params,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "X-EBAY-C-MARKETPLACE-ID": self.settings.ebay_marketplace_id,
                        "Accept-Language": "fr-FR",
                    },
                )
            except httpx.HTTPError as exc:
                raise ConnectorError(f"eBay injoignable ({type(exc).__name__}).") from exc
        if response.status_code in (401, 403):
            raise ConnectorError(
                "Accès à la Browse API refusé par eBay. En production, les Buy APIs peuvent "
                "exiger une approbation eBay Partner Network (voir docs/connectors.md). "
                f"Détail eBay : {ebay_error_message(response) or 'aucun'}"
            )
        if response.status_code == 429:
            raise ConnectorError("Quota eBay atteint : nouvelle tentative plus tard.")
        if response.status_code != 200:
            detail = ebay_error_message(response)
            raise ConnectorError(f"Recherche eBay en erreur (HTTP {response.status_code}) {detail}")
        observed_at = datetime.now(UTC)
        items = response.json().get("itemSummaries") or []
        offers = [to_raw_offer(item, observed_at) for item in items]
        return [o for o in offers if o is not None]

    async def fetch_offer(self, external_id: str) -> RawOffer | None:
        return None  # getItem non utilisé à ce stade
