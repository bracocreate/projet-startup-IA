"""Catalogue : marchands, produits, variantes, offres et observations de prix (Phase 3).

Distinctions du cahier des charges §3.1 :
- Produit = identité générique ; Variante = taille/couleur ; Offre = proposition d'un marchand via
  une source ; Observation = prix constaté à un instant précis (historique de prix).
- Aucune fusion de produits sur simple ressemblance de titre : seuls GTIN ou (marque + référence
  fabricant) permettent de rattacher une offre à un produit existant (`match_method`).
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPkMixin
from app.models.source import AccessMethod, Source

PRICE = Numeric(14, 2)
RATE = Numeric(18, 8)


class Availability(enum.StrEnum):
    in_stock = "in_stock"
    out_of_stock = "out_of_stock"
    unknown = "unknown"


class Condition(enum.StrEnum):
    new = "new"
    used = "used"
    refurbished = "refurbished"
    unknown = "unknown"


class MatchMethod(enum.StrEnum):
    gtin = "gtin"
    brand_mpn = "brand_mpn"
    new_product = "new_product"


class RunStatus(enum.StrEnum):
    running = "running"
    success = "success"
    partial = "partial"
    error = "error"


class Merchant(UUIDPkMixin, TimestampMixin, Base):
    """Vendeur ou fournisseur. Identifié par une clé normalisée (nom + pays)."""

    __tablename__ = "merchants"

    key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country: Mapped[str | None] = mapped_column(String(2))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Product(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "products"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(120))
    # Clé de comparaison de la marque (minuscules, espaces normalisés).
    brand_key: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(200))
    mpn: Mapped[str | None] = mapped_column(String(120))
    gtin: Mapped[str | None] = mapped_column(String(14))
    category: Mapped[str | None] = mapped_column(String(200))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product")

    __table_args__ = (
        Index("uq_products_gtin", "gtin", unique=True, postgresql_where="gtin IS NOT NULL"),
        Index(
            "uq_products_brand_key_mpn",
            "brand_key",
            "mpn",
            unique=True,
            postgresql_where="brand_key IS NOT NULL AND mpn IS NOT NULL",
        ),
    )


class ProductVariant(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "product_variants"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    size: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    color: Mapped[str] = mapped_column(String(80), default="", nullable=False)

    product: Mapped[Product] = relationship(back_populates="variants")

    __table_args__ = (UniqueConstraint("product_id", "size", "color"),)


class ConnectorRun(UUIDPkMixin, Base):
    """Exécution d'un connecteur : traçabilité de chaque collecte (succès, partiel, erreur)."""

    __tablename__ = "connector_runs"

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, name="run_status"), default=RunStatus.running, nullable=False
    )
    actor: Mapped[str] = mapped_column(String(80), nullable=False)
    query: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    offers_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    offers_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    offers_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    observations_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    source: Mapped[Source] = relationship()


class Offer(UUIDPkMixin, TimestampMixin, Base):
    """Offre d'un marchand, telle que connue au dernier passage du connecteur."""

    __tablename__ = "offers"

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(200), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="SET NULL")
    )
    merchant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    condition: Mapped[Condition] = mapped_column(
        Enum(Condition, name="offer_condition"), default=Condition.unknown, nullable=False
    )
    country: Mapped[str | None] = mapped_column(String(2))
    # Prix affiché, dans la devise d'origine.
    price_amount: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    # Conversion EUR : NULL si aucun taux n'est configuré (jamais de taux inventé).
    price_eur: Mapped[Decimal | None] = mapped_column(PRICE)
    fx_rate_to_eur: Mapped[Decimal | None] = mapped_column(RATE)
    # Frais de livraison : NULL = inconnus (≠ 0 = gratuits).
    shipping_amount: Mapped[Decimal | None] = mapped_column(PRICE)
    availability: Mapped[Availability] = mapped_column(
        Enum(Availability, name="availability"), default=Availability.unknown, nullable=False
    )
    access_method: Mapped[AccessMethod] = mapped_column(
        Enum(AccessMethod, name="access_method", create_type=False), nullable=False
    )
    match_method: Mapped[MatchMethod] = mapped_column(
        Enum(MatchMethod, name="match_method"), nullable=False
    )
    match_confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    source: Mapped[Source] = relationship()
    product: Mapped[Product] = relationship()
    variant: Mapped[ProductVariant | None] = relationship()
    merchant: Mapped[Merchant | None] = relationship()
    observations: Mapped[list["OfferObservation"]] = relationship(
        back_populates="offer", order_by="OfferObservation.observed_at"
    )

    __table_args__ = (
        UniqueConstraint("source_id", "external_id"),
        Index("ix_offers_product_id", "product_id"),
        Index("ix_offers_last_seen_at", "last_seen_at"),
        CheckConstraint("price_amount >= 0", name="price_non_negative"),
        CheckConstraint("match_confidence BETWEEN 0 AND 1", name="confidence_range"),
    )


class OfferObservation(UUIDPkMixin, Base):
    """Prix et disponibilité constatés à un instant donné. Une ligne par changement observé."""

    __tablename__ = "offer_observations"

    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("offers.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("connector_runs.id", ondelete="SET NULL")
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price_amount: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    price_eur: Mapped[Decimal | None] = mapped_column(PRICE)
    shipping_amount: Mapped[Decimal | None] = mapped_column(PRICE)
    availability: Mapped[Availability] = mapped_column(
        Enum(Availability, name="availability", create_type=False), nullable=False
    )

    offer: Mapped[Offer] = relationship(back_populates="observations")

    __table_args__ = (Index("ix_offer_observations_offer_observed", "offer_id", "observed_at"),)
