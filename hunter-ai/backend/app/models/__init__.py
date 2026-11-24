"""Modèles SQLAlchemy. Phase 1 : socle minimal (utilisateur, paramètres, sources, audit).

Les entités métier (produits, offres, opportunités…) arrivent en Phase 3+ via de nouvelles
migrations Alembic.
"""

from app.models.audit_log import AuditLog
from app.models.catalog import (
    Availability,
    Condition,
    ConnectorRun,
    MatchMethod,
    Merchant,
    Offer,
    OfferObservation,
    Product,
    ProductVariant,
    RunStatus,
)
from app.models.source import AccessMethod, Source, SourceStatus
from app.models.user import User, UserSettings

__all__ = [
    "AccessMethod",
    "AuditLog",
    "Availability",
    "Condition",
    "ConnectorRun",
    "MatchMethod",
    "Merchant",
    "Offer",
    "OfferObservation",
    "Product",
    "ProductVariant",
    "RunStatus",
    "Source",
    "SourceStatus",
    "User",
    "UserSettings",
]
