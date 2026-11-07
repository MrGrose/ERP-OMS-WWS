from sqlalchemy import select
from sqlalchemy.orm import Session

from erp_oms_wms.domains.audit.models import AuditLog


def record(
    session: Session,
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    details: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    session.add(entry)
    session.flush()
    return entry


def list_for_entity(
    session: Session,
    *,
    entity_type: str,
    entity_id: str,
    limit: int = 100,
) -> list[AuditLog]:
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id,
        )
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(stmt))
