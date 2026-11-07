from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from erp_oms_wms.api import schemas
from erp_oms_wms.api.deps import get_db
from erp_oms_wms.api.rbac import UserRole, require_permission
from erp_oms_wms.domains.payments import service as payment_service
from erp_oms_wms.domains.payments.errors import InvalidPaymentTransitionError, PaymentError

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/attempts", response_model=schemas.PaymentAttemptOut, status_code=201)
def create_payment_attempt(
    body: schemas.PaymentAttemptCreateIn,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("payments.read")),
) -> schemas.PaymentAttemptOut:
    try:
        attempt = payment_service.create_attempt(session, body.invoice_id, provider=body.provider)
        session.refresh(attempt)
        return schemas.PaymentAttemptOut.model_validate(attempt)
    except PaymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/webhook", response_model=schemas.PaymentAttemptOut)
def payment_webhook(
    body: schemas.PaymentWebhookIn,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("payments.read")),
) -> schemas.PaymentAttemptOut:
    try:
        attempt = payment_service.apply_webhook(
            session,
            payment_attempt_id=body.payment_attempt_id,
            external_event_id=body.external_event_id,
            succeeded=body.succeeded,
            failure_reason=body.failure_reason,
        )
        session.refresh(attempt)
        return schemas.PaymentAttemptOut.model_validate(attempt)
    except InvalidPaymentTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PaymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
