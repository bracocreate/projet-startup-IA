import enum

from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPkMixin


class SourceStatus(enum.StrEnum):
    planned = "planned"
    needs_credentials = "needs_credentials"
    needs_approval = "needs_approval"
    active = "active"
    degraded = "degraded"
    disabled = "disabled"
    blocked_by_terms = "blocked_by_terms"
    error = "error"


class AccessMethod(enum.StrEnum):
    official_api = "official_api"
    affiliate_feed = "affiliate_feed"
    licensed_provider = "licensed_provider"
    newsletter = "newsletter"
    manual_import = "manual_import"
    permitted_automation = "permitted_automation"
    unknown = "unknown"


class Source(UUIDPkMixin, TimestampMixin, Base):
    """Source de données (site, API, flux, newsletter, fournisseur…)."""

    __tablename__ = "sources"

    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    family: Mapped[str] = mapped_column(String(64), nullable=False)
    country: Mapped[str | None] = mapped_column(String(8))
    homepage_url: Mapped[str | None] = mapped_column(String(500))
    access_method: Mapped[AccessMethod] = mapped_column(
        Enum(AccessMethod, name="access_method"), default=AccessMethod.unknown, nullable=False
    )
    status: Mapped[SourceStatus] = mapped_column(
        Enum(SourceStatus, name="source_status"), default=SourceStatus.planned, nullable=False
    )
    terms_notes: Mapped[str | None] = mapped_column(Text)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
