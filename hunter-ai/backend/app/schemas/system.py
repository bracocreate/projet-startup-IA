from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class HealthRead(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "error"]
    version: str
    time_utc: datetime


class ComponentStatus(BaseModel):
    name: str
    status: Literal["ok", "warning", "error", "not_configured", "not_implemented"]
    detail: str


class SystemStatusRead(BaseModel):
    version: str
    environment: str
    timezone: str
    time_utc: datetime
    db_revision: str | None
    db_revision_expected: str | None
    components: list[ComponentStatus]


class SourceRead(BaseModel):
    id: str
    slug: str
    name: str
    family: str
    country: str | None
    access_method: str
    status: str
    is_demo: bool


class RankingSection(BaseModel):
    key: Literal["best_deals", "emerging_trends", "new_markets"]
    title: str
    status: Literal["empty", "not_implemented"]
    message: str
    items: list[dict[str, object]]


class DashboardSummaryRead(BaseModel):
    generated_at: datetime
    data_mode: Literal["empty", "demo", "live"]
    last_refresh_at: datetime | None
    is_stale: bool
    stale_after_hours: int
    sources_total: int
    offers_total: int
    sources_by_status: dict[str, int]
    sources_in_error: list[SourceRead]
    pending_discoveries: int
    rankings: list[RankingSection]
