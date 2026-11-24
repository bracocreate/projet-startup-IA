"""Connecteur AliExpress Affiliate API (accès officiel, lecture seule).

Vérifié le 24/11/2026 :
- Méthode `aliexpress.affiliate.product.query` (référence officielle openservice.aliexpress.com) :
  keywords, page_no, page_size (1–50), sort (SALE_PRICE_ASC/DESC, LAST_VOLUME_ASC/DESC),
  target_currency (EUR), target_language (FR), ship_to_country (« filtre les produits livrables
  dans ce pays ; prix selon la politique fiscale du pays »), tracking_id.
- Appel « métier » : GET https://api-sg.aliexpress.com/sync?method=…, paramètres communs
  app_key, timestamp (millisecondes), sign_method=sha256, sign = HMAC-SHA256 (clé : App Secret)
  de la concaténation nom+valeur des paramètres triés (valeurs vides exclues), en hexadécimal
  majuscule. Vecteur de test officiel reproduit dans les tests.

Choix prudents :
- `max_sale_price` n'est pas envoyé (unité documentée ambiguë : « unit cent ») : le prix maximum
  est filtré localement, sur le prix renvoyé ;
- lien public de la fiche produit (`product_detail_url`), jamais le lien d'affiliation : utiliser
  son propre lien d'affiliation pour ses achats est en général interdit par les programmes ;
- frais de livraison non fournis par cette méthode → « inconnus » ; disponibilité « à confirmer » ;
- quota officiel non documenté publiquement : plafond de sécurité configurable côté HUNTER AI.
"""

import hashlib
import hmac
import time
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
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

ALIEXPRESS_SLUG = "aliexpress"
GATEWAY = "https://api-sg.aliexpress.com/sync"
METHOD = "aliexpress.affiliate.product.query"
MAX_PAGE_SIZE = 50
TIMEOUT = httpx.Timeout(20.0)


def sign_params(params: dict[str, str], secret: str, api_path: str = "") -> str:
    """Signature IOP : HMAC-SHA256(secret, [api_path] + concat(nom+valeur triés)) en HEX majuscule.

    `api_path` n'est utilisé que pour les API « système » (/auth/...) ; vide pour les API métier.
    """
    payload = api_path + "".join(
        f"{key}{params[key]}" for key in sorted(params) if key != "sign" and params[key] != ""
    )
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest().upper()


def decimal_or_none(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value)) if value not in (None, "") else None
    except InvalidOperation:
        return None


def products_from(body: dict[str, Any]) -> list[dict[str, Any]]:
    """Extrait la liste de produits ; accepte les formats « simplifié » et « complet »."""
    if "error_response" in body:
        error = body["error_response"] or {}
        code = str(error.get("code") or "")
        message = str(error.get("msg") or error.get("message") or "")[:200]
        lowered = code.lower()
        if "appkey" in lowered or "signature" in lowered or "secret" in lowered:
            raise ConnectorError(
                f"AliExpress refuse les identifiants (vérifiez App Key et App Secret) : {code}"
            )
        if "permission" in lowered or "forbidden" in lowered or "unauthorized" in lowered:
            raise ConnectorError(
                f"Accès à l'API d'affiliation refusé par AliExpress ({code}) : vérifiez que "
                "l'application a bien l'autorisation « Affiliate API »."
            )
        if "limit" in lowered or "flow" in lowered:
            raise ConnectorError(f"Quota AliExpress atteint ({code}) : réessayez plus tard.")
        raise ConnectorError(f"Erreur AliExpress {code} {message}".strip())
    container = body
    for key, value in body.items():
        if key.endswith("_response") and isinstance(value, dict):
            container = value
    resp = container.get("resp_result") or {}
    resp_code = str(resp.get("resp_code") or "")
    if resp_code and resp_code != "200":
        raise ConnectorError(f"AliExpress a répondu {resp_code} : {resp.get('resp_msg') or ''}")
    products = (resp.get("result") or {}).get("products") or []
    if isinstance(products, dict):  # format complet : {"product": [...]}
        products = products.get("product") or []
    return [p for p in products if isinstance(p, dict)]


def to_raw_offer(item: dict[str, Any], observed_at: datetime) -> RawOffer | None:
    price = decimal_or_none(item.get("target_sale_price"))
    currency = item.get("target_sale_price_currency")
    if price is None or not currency:  # repli sur le prix d'origine
        price = decimal_or_none(item.get("sale_price"))
        currency = item.get("sale_price_currency")
    url = item.get("product_detail_url")
    if not item.get("product_id") or price is None or not currency or not url:
        return None
    extra = {
        k: str(item[k])
        for k in ("evaluate_rate", "lastest_volume", "shop_id", "ship_to_days", "discount")
        if item.get(k) not in (None, "")
    }
    return RawOffer(
        external_id=str(item["product_id"]),
        title=str(item.get("product_title") or ""),
        url=str(url),
        price=price,
        currency=str(currency),
        observed_at=observed_at,
        availability="unknown",
        condition="new",
        shipping_cost=None,
        # Boutique professionnelle (nom commercial), pas une personne physique.
        merchant_name=item.get("shop_name") or None,
        category=item.get("second_level_category_name") or item.get("first_level_category_name"),
        extra=extra,
    )


class AliExpressConnector:
    source_slug = ALIEXPRESS_SLUG

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.transport = transport
        self.api_calls = 0

    def signed_params(self, business: dict[str, str]) -> dict[str, str]:
        params = {
            "method": METHOD,
            "app_key": self.settings.aliexpress_app_key,
            "sign_method": "sha256",
            "timestamp": str(int(time.time() * 1000)),
            **{k: v for k, v in business.items() if v != ""},
        }
        params["sign"] = sign_params(params, self.settings.aliexpress_app_secret.get_secret_value())
        return params

    def business_params(self, query: SearchQuery) -> dict[str, str]:
        keywords = " ".join(filter(None, [query.brand, query.keywords])).strip()
        if not keywords:
            raise ConnectorError("Recherche AliExpress : indiquez des mots-clés ou une marque.")
        return {
            "keywords": keywords[:100],
            "page_no": "1",
            "page_size": str(max(1, min(query.limit, MAX_PAGE_SIZE))),
            "target_currency": "EUR",
            "target_language": "FR",
            "ship_to_country": "FR",
            "tracking_id": self.settings.aliexpress_tracking_id,
        }

    async def health_check(self) -> SourceHealth:
        if not self.settings.aliexpress_configured:
            return SourceHealth(
                ok=False, detail="Identifiants AliExpress non configurés dans .env."
            )
        return SourceHealth(ok=True, detail="Identifiants AliExpress présents.")

    async def get_capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            access_method=AccessMethod.official_api,
            supports_search=True,
            supports_fetch_offer=False,
            supports_gtin_search=False,
            max_results_per_query=MAX_PAGE_SIZE,
            min_interval_seconds=1,
            is_demo=False,
            limits="50 produits par page ; frais de port non fournis ; quota officiel non "
            "publié (plafond de sécurité HUNTER AI).",
        )

    async def search(self, query: SearchQuery) -> list[RawOffer]:
        params = self.signed_params(self.business_params(query))
        async with httpx.AsyncClient(timeout=TIMEOUT, transport=self.transport) as client:
            self.api_calls += 1
            try:
                response = await client.get(GATEWAY, params=params)
            except httpx.HTTPError as exc:
                raise ConnectorError(f"AliExpress injoignable ({type(exc).__name__}).") from exc
        if response.status_code != 200:
            raise ConnectorError(f"AliExpress en erreur (HTTP {response.status_code}).")
        try:
            body = response.json()
        except ValueError as exc:
            raise ConnectorError("Réponse AliExpress illisible (JSON invalide).") from exc
        observed_at = datetime.now(UTC)
        offers = [to_raw_offer(p, observed_at) for p in products_from(body)]
        result = [o for o in offers if o is not None]
        if query.max_price is not None:
            result = [o for o in result if o.currency == "EUR" and o.price <= query.max_price]
        return result

    async def fetch_offer(self, external_id: str) -> RawOffer | None:
        return None
