import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import redact_mapping
from app.models import AuditLog

logger = logging.getLogger("hunter.audit")


def record_audit(
    db: Session,
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    """Ajoute une entrée au journal d'audit (le commit reste à l'appelant)."""
    safe = redact_mapping(details or {})
    entry = AuditLog(
        actor=actor, action=action, entity_type=entity_type, entity_id=entity_id, details=safe
    )
    db.add(entry)
    logger.info("audit", extra={"action": action, "entity_type": entity_type})
    return entry
