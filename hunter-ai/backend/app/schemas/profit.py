from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Money = Decimal


class ProfitRequest(BaseModel):
    """Saisie du calculateur. Tous les montants en EUR. Transport vide = inconnu."""

    model_config = ConfigDict(extra="forbid")

    unit_price: Money = Field(ge=0, le=1_000_000)
    quantity: int = Field(default=1, ge=1, le=100_000)
    shipping_cost: Money | None = Field(default=None, ge=0, le=1_000_000)
    origin: Literal["eu", "non_eu"] = "eu"
    article_categories: int = Field(default=1, ge=1, le=100)
    vat_status: Literal["included", "not_included", "unknown"] = "unknown"
    vat_rate_pct: Decimal = Field(default=Decimal(20), ge=0, le=100)
    customs_duty_rate_pct: Decimal | None = Field(default=None, ge=0, le=100)
    payment_fee_pct: Decimal = Field(default=Decimal(0), ge=0, le=100)
    other_fixed_costs: Money = Field(default=Decimal(0), ge=0, le=1_000_000)
    prep_cost_per_unit: Money = Field(default=Decimal(0), ge=0, le=10_000)
    defect_rate_pct: Decimal = Field(default=Decimal(0), ge=0, le=100)
    resale_low: Money | None = Field(default=None, ge=0, le=1_000_000)
    resale_central: Money | None = Field(default=None, ge=0, le=1_000_000)
    resale_high: Money | None = Field(default=None, ge=0, le=1_000_000)
    selling_fee_pct: Decimal = Field(default=Decimal(0), ge=0, le=100)
    selling_fee_fixed_per_unit: Money = Field(default=Decimal(0), ge=0, le=10_000)
    selling_shipping_per_unit: Money = Field(default=Decimal(0), ge=0, le=10_000)
    target_roi_pct: Decimal = Field(default=Decimal(30), ge=-100, le=10_000)
    branded: bool = False


class AmountRead(BaseModel):
    low: Decimal
    high: Decimal


class CostLineRead(BaseModel):
    key: str
    label: str
    status: Literal["known", "range", "unknown"]
    amount: AmountRead | None
    basis: str


class ScenarioRead(BaseModel):
    key: Literal["pessimistic", "central", "optimistic"]
    resale_price: Decimal
    cost_used: Decimal
    revenue: Decimal
    selling_costs: Decimal
    profit: Decimal
    roi_pct: Decimal | None
    margin_pct: Decimal | None


class ProfitResultRead(BaseModel):
    lines: list[CostLineRead]
    landed_cost: AmountRead | None
    landed_cost_per_unit: AmountRead | None
    sellable_units: Decimal
    cost_per_sellable_unit: AmountRead | None
    scenarios: list[ScenarioRead]
    break_even_price: Decimal | None
    max_unit_price_for_target: Decimal | None
    missing: list[str]
    warnings: list[str]
    rules_version: str


class ResaleRecordCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=300)
    brand: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=120)
    size: str | None = Field(default=None, max_length=40)
    condition: str | None = Field(default=None, max_length=40)
    channel: Literal["vinted", "ebay", "leboncoin", "other"] = "vinted"
    sale_price: Money = Field(ge=0, le=1_000_000)
    platform_fees: Money | None = Field(default=None, ge=0, le=1_000_000)
    shipping_paid: Money | None = Field(default=None, ge=0, le=1_000_000)
    purchase_cost: Money | None = Field(default=None, ge=0, le=1_000_000)
    sold_on: date
    notes: str | None = Field(default=None, max_length=2000)


class ResaleRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    brand: str | None
    category: str | None
    size: str | None
    condition: str | None
    channel: str
    sale_price: Decimal
    platform_fees: Decimal | None
    shipping_paid: Decimal | None
    purchase_cost: Decimal | None
    # Bénéfice réel, seulement si coût d'achat, frais et port sont tous renseignés.
    real_profit: Decimal | None
    sold_on: date
    notes: str | None
    created_at: datetime


class ResaleRecordPage(BaseModel):
    items: list[ResaleRecordRead]
    total: int
    limit: int
    offset: int


class ResaleReferenceRead(BaseModel):
    """Référence de prix tirée de VOS ventes réalisées. `enough` = au moins 3 ventes."""

    count: int
    enough: bool
    minimum: Decimal | None
    low: Decimal | None  # 1er quartile
    median: Decimal | None
    high: Decimal | None  # 3e quartile
    maximum: Decimal | None
    brand: str | None
    q: str | None
