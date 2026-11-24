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
- frais de port : méthode officielle `aliexpress.affiliate.product.shipping.get` (product_id,
  sku_id, ship_to_country, target_currency, target_sale_price, target_language, tax_rate →
  shipping_fee, délais, ship_from_country), pour les N premiers produits seulement (1 appel
  chacun) ; un échec laisse les frais « inconnus » sans bloquer la collecte ;
- disponibilité « à confirmer » ;
- quota officiel non documenté publiquement : plafond de sécurité configurable côté HUNTER AI.
"""

import dataclasses
import hashlib
import hmac
import time
from dataclasses import dataclass
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
SHIPPING_METHOD = "aliexpress.affiliate.product.shipping.get"
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


def resp_result(body: dict[str, Any]) -> dict[str, Any]:
    """Extrait `resp_result` (formats « simplifié » et « complet ») ou lève une erreur explicite."""
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
    return resp if isinstance(resp, dict) else {}


def products_from(body: dict[str, Any]) -> list[dict[str, Any]]:
    products = (resp_result(body).get("result") or {}).get("products") or []
    if isinstance(products, dict):  # format complet : {"product": [...]}
        products = products.get("product") or []
    return [p for p in products if isinstance(p, dict)]


@dataclass(frozen=True)
class ShippingInfo:
    fee: Decimal | None
    ship_from_country: str | None
    delivery_days: str | None


def shipping_from(body: dict[str, Any]) -> ShippingInfo:
    result = resp_result(body).get("result") or {}
    country = str(result.get("ship_from_country") or "").strip().upper() or None
    days = result.get("delivery_days") or result.get("max_delivery_days")
    return ShippingInfo(
        fee=decimal_or_none(result.get("shipping_fee")),
        ship_from_country=country,
        delivery_days=str(days) if days not in (None, "") else None,
    )


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
        for k in (
            "evaluate_rate",
            "lastest_volume",
            "shop_id",
            "ship_to_days",
            "discount",
            "sku_id",
            "tax_rate",
        )
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
        self.warnings: list[str] = []

    def signed_params(self, business: dict[str, str], method: str = METHOD) -> dict[str, str]:
        params = {
            "method": method,
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
            limits="50 produits par page ; frais de port réels pour les N premiers produits "
            "(1 appel chacun) ; quota officiel non publié (plafond de sécurité HUNTER AI).",
        )

    async def call(self, method: str, business: dict[str, str]) -> dict[str, Any]:
        params = self.signed_params(business, method)
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
        return body if isinstance(body, dict) else {}

    async def shipping(self, offer: RawOffer) -> ShippingInfo | None:
        """Frais de port réels vers la France (méthode officielle). None si non applicable."""
        sku_id, tax_rate = offer.extra.get("sku_id"), offer.extra.get("tax_rate")
        if not sku_id or tax_rate is None or offer.currency != "EUR":
            return None
        body = await self.call(
            SHIPPING_METHOD,
            {
                "product_id": offer.external_id,
                "sku_id": sku_id,
                "ship_to_country": "FR",
                "target_currency": "EUR",
                "target_sale_price": str(offer.price),
                "target_language": "FR",
                "tax_rate": tax_rate,
            },
        )
        return shipping_from(body)

    async def with_shipping(self, offer: RawOffer) -> RawOffer:
        try:
            info = await self.shipping(offer)
        except ConnectorError as exc:
            self.warnings.append(f"{offer.external_id} : frais de port non obtenus ({exc})")
            return offer
        if info is None:
            return offer
        extra = dict(offer.extra)
        if info.delivery_days:
            extra["delivery_days"] = info.delivery_days
        return dataclasses.replace(
            offer,
            # Montant demandé en EUR (target_currency) ; absent → reste « inconnu ».
            shipping_cost=info.fee,
            # Pays d'expédition : décisif pour les droits (entrepôt UE = pas de douane).
            country=info.ship_from_country or offer.country,
            extra=extra,
        )

    async def search(self, query: SearchQuery) -> list[RawOffer]:
        body = await self.call(METHOD, self.business_params(query))
        observed_at = datetime.now(UTC)
        offers = [o for o in (to_raw_offer(p, observed_at) for p in products_from(body)) if o]
        if query.max_price is not None:
            offers = [o for o in offers if o.currency == "EUR" and o.price <= query.max_price]
        lookups = self.settings.aliexpress_shipping_lookups_per_run
        enriched = [await self.with_shipping(o) for o in offers[:lookups]]
        return enriched + offers[lookups:]

    async def fetch_offer(self, external_id: str) -> RawOffer | None:
        return None
