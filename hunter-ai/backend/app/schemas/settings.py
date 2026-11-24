from datetime import datetime, time
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    app_name: str
    language: str
    currency: str
    timezone: str
    max_item_budget_eur: Decimal | None
    max_lot_budget_eur: Decimal | None
    daily_collection_start: time
    daily_collection_duration_min: int
    markets: list[str]
    priority_brands: list[str]
    buy_unit: bool
    buy_lots: bool
    telegram_enabled: bool
    auto_purchase_allowed: bool
    updated_at: datetime


class SettingsUpdate(BaseModel):
    """Champs modifiables. `auto_purchase_allowed` n'est volontairement pas modifiable."""

    model_config = ConfigDict(extra="forbid")

    timezone: str | None = None
    max_item_budget_eur: Decimal | None = Field(default=None, ge=0, le=1_000_000)
    max_lot_budget_eur: Decimal | None = Field(default=None, ge=0, le=10_000_000)
    daily_collection_start: time | None = None
    daily_collection_duration_min: int | None = Field(default=None, ge=5, le=12 * 60)
    markets: list[str] | None = Field(default=None, max_length=50)
    priority_brands: list[str] | None = Field(default=None, max_length=200)
    buy_unit: bool | None = None
    buy_lots: bool | None = None
    telegram_enabled: bool | None = None

    @field_validator("timezone")
    @classmethod
    def _valid_tz(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Fuseau horaire inconnu") from exc
        return v

    @field_validator("markets", "priority_brands")
    @classmethod
    def _clean_list(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        cleaned: list[str] = []
        for item in v:
            s = item.strip()
            if not s:
                continue
            if len(s) > 80:
                raise ValueError("Élément trop long (80 caractères max.)")
            if s not in cleaned:
                cleaned.append(s)
        return cleaned
