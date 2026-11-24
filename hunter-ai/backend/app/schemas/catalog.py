from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class SourceRef(BaseModel):
    slug: str
    name: str
    is_demo: bool


class MerchantRef(BaseModel):
    name: str
    country: str | None


class OfferRead(BaseModel):
    id: str
    title: str
    url: str
    source: SourceRef
    merchant: MerchantRef | None
    product_id: str
    brand: str | None
    gtin: str | None
    mpn: str | None
    size: str | None
    color: str | None
    condition: str
    country: str | None
    # Prix affiché dans la devise d'origine.
    price_amount: Decimal
    currency: str
    # None = conversion impossible (taux non configuré) → « non déterminé ».
    price_eur: Decimal | None
    fx_rate_to_eur: Decimal | None
    # None = frais de livraison inconnus (≠ 0 = gratuits).
    shipping_amount: Decimal | None
    # Prix + livraison en EUR, seulement si les deux sont connus.
    price_with_shipping_eur: Decimal | None
    availability: Literal["in_stock", "out_of_stock", "unknown"]
    first_seen_at: datetime
    last_verified_at: datetime
    is_stale: bool
    access_method: str
    match_method: Literal["gtin", "brand_mpn", "new_product"]
    match_confidence: Decimal
    is_demo: bool


class ObservationRead(BaseModel):
    observed_at: datetime
    price_amount: Decimal
    currency: str
    price_eur: Decimal | None
    shipping_amount: Decimal | None
    availability: str


class OfferDetailRead(OfferRead):
    observations: list[ObservationRead]


class OfferPage(BaseModel):
    items: list[OfferRead]
    total: int
    limit: int
    offset: int


class PricePoint(ObservationRead):
    offer_id: str
    merchant: str | None
    source: str


class PriceHistoryRead(BaseModel):
    product_id: str
    title: str
    brand: str | None
    gtin: str | None
    is_demo: bool
    offers_count: int
    points: list[PricePoint]


class ConnectorRunRead(BaseModel):
    id: str
    source: SourceRef
    status: Literal["running", "success", "partial", "error"]
    actor: str
    started_at: datetime
    finished_at: datetime | None
    offers_received: int
    offers_created: int
    offers_updated: int
    observations_created: int
    errors: list[str]
    is_demo: bool


class DemoPurgeRead(BaseModel):
    offers_deleted: int
    products_deleted: int
    merchants_deleted: int
    sources_deleted: int
