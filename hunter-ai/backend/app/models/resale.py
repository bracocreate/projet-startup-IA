"""Ventes réellement réalisées, saisies par l'utilisateur (prix réalisés, jamais estimés)."""

import enum
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, Enum, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPkMixin


class SaleChannel(enum.StrEnum):
    vinted = "vinted"
    ebay = "ebay"
    leboncoin = "leboncoin"
    other = "other"


class ResaleRecord(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "resale_records"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(120))
    brand_key: Mapped[str | None] = mapped_column(String(120))
    category: Mapped[str | None] = mapped_column(String(120))
    size: Mapped[str | None] = mapped_column(String(40))
    condition: Mapped[str | None] = mapped_column(String(40))
    channel: Mapped[SaleChannel] = mapped_column(
        Enum(SaleChannel, name="sale_channel"), nullable=False
    )
    # Prix de vente réalisé (payé par l'acheteur pour l'article, hors frais acheteur).
    sale_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # Frais prélevés par la plateforme et port payé par vous : None = non renseigné.
    platform_fees: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    shipping_paid: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    purchase_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    sold_on: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("ix_resale_records_brand_key", "brand_key"),
        Index("ix_resale_records_sold_on", "sold_on"),
        CheckConstraint("sale_price >= 0", name="sale_price_non_negative"),
    )
