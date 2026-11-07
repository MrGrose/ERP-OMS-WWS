from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from erp_oms_wms.api import schemas
from erp_oms_wms.api.deps import get_db
from erp_oms_wms.api.rbac import UserRole, require_roles
from erp_oms_wms.domains.audit import service as audit_service

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=list[schemas.AuditLogOut])
def list_audit_logs(
    entity_type: str,
    entity_id: str,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.ACCOUNTANT)),
) -> list[schemas.AuditLogOut]:
    logs = audit_service.list_for_entity(session, entity_type=entity_type, entity_id=entity_id)
    return [schemas.AuditLogOut.model_validate(entry) for entry in logs]
