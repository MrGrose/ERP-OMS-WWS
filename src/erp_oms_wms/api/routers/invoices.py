from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from erp_oms_wms.api import schemas
from erp_oms_wms.api.deps import get_db
from erp_oms_wms.api.rbac import UserRole, require_permission
from erp_oms_wms.domains.invoices import service as invoice_service
from erp_oms_wms.domains.invoices.errors import InvalidInvoiceTransitionError, InvoiceError

router = APIRouter(prefix="/invoices", tags=["invoices"])


# Выставляет счёт по заказу в RESERVED.
@router.post("", response_model=schemas.InvoiceOut, status_code=201)
def issue_invoice(
    body: schemas.InvoiceIssueIn,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("finance.read")),
) -> schemas.InvoiceOut:
    try:
        invoice = invoice_service.issue_for_order(
            session,
            body.order_id,
            amount_cents=body.amount_cents,
            currency=body.currency,
            payment_deadline_hours=body.payment_deadline_hours,
        )
        session.refresh(invoice)
        return schemas.InvoiceOut.model_validate(invoice)
    except InvalidInvoiceTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InvoiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
