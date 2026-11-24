import uuid
from datetime import time
from decimal import Decimal

from sqlalchemy import ARRAY, Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPkMixin

DEFAULT_PRIORITY_BRANDS = [
    "Nike",
    "Adidas",
    "Ralph Lauren",
    "Lacoste",
    "The North Face",
    "Tommy Hilfiger",
]
DEFAULT_MARKETS = ["FR", "EU", "CN", "ASIA", "US", "UK"]


class User(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120))

    settings: Mapped["UserSettings"] = relationship(back_populates="user", uselist=False)


class UserSettings(UUIDPkMixin, TimestampMixin, Base):
    """Paramètres métier modifiables (section 2 du cahier des charges)."""

    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    app_name: Mapped[str] = mapped_column(String(80), default="HUNTER AI", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="fr", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Paris", nullable=False)
    max_item_budget_eur: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), default=Decimal("100.00")
    )
    max_lot_budget_eur: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=None)
    daily_collection_start: Mapped[time] = mapped_column(Time, default=time(6, 0), nullable=False)
    daily_collection_duration_min: Mapped[int] = mapped_column(Integer, default=120, nullable=False)
    markets: Mapped[list[str]] = mapped_column(ARRAY(String(16)), default=list, nullable=False)
    priority_brands: Mapped[list[str]] = mapped_column(
        ARRAY(String(80)), default=list, nullable=False
    )
    buy_unit: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    buy_lots: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Garde-fou : l'achat automatique est interdit par conception et non modifiable via l'API.
    auto_purchase_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship(back_populates="settings")

    __table_args__ = (CheckConstraint("auto_purchase_allowed = false", name="no_auto_purchase"),)
