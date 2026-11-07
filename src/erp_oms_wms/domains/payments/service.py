from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from erp_oms_wms.domains.invoices import service as invoice_service
from erp_oms_wms.domains.invoices.enums import InvoiceStatus
from erp_oms_wms.domains.invoices.models import Invoice
from erp_oms_wms.domains.orders import service as order_service
from erp_oms_wms.domains.payments.enums import PaymentAttemptStatus
from erp_oms_wms.domains.payments.errors import (
    InvalidPaymentTransitionError,
    PaymentAttemptNotFoundError,
)
from erp_oms_wms.domains.payments.models import PaymentAttempt


# Создаёт попытку оплаты и переводит в PENDING.
def create_attempt(session: Session, invoice_id: str, *, provider: str = "mock") -> PaymentAttempt:
    invoice = session.get(Invoice, invoice_id)
    if invoice is None:
        raise PaymentAttemptNotFoundError(invoice_id)
    if invoice.status != InvoiceStatus.PENDING_PAYMENT:
        raise InvalidPaymentTransitionError("invoice not payable")
    attempt = PaymentAttempt(
        invoice_id=invoice_id,
        amount_cents=invoice.amount_cents,
        currency=invoice.currency,
        provider=provider,
        status=PaymentAttemptStatus.CREATED,
    )
    session.add(attempt)
    session.flush()
    attempt.status = PaymentAttemptStatus.PENDING
    session.flush()
    return attempt


# Обрабатывает webhook платежа с идемпотентностью по external_event_id.
def apply_webhook(
    session: Session,
    *,
    payment_attempt_id: str,
    external_event_id: str,
    succeeded: bool,
    failure_reason: str | None = None,
) -> PaymentAttempt:
    existing = session.scalars(
        select(PaymentAttempt).where(PaymentAttempt.external_event_id == external_event_id),
    ).first()
    if existing is not None:
        return existing

    attempt = session.get(PaymentAttempt, payment_attempt_id)
    if attempt is None:
        raise PaymentAttemptNotFoundError(payment_attempt_id)
    if attempt.status not in (
        PaymentAttemptStatus.PENDING,
        PaymentAttemptStatus.SUCCEEDED,
        PaymentAttemptStatus.FAILED,
    ):
        raise InvalidPaymentTransitionError(attempt.status.value)
    if attempt.status in (PaymentAttemptStatus.SUCCEEDED, PaymentAttemptStatus.FAILED):
        return attempt

    attempt.external_event_id = external_event_id
    try:
        with session.begin_nested():
            session.flush()
    except IntegrityError:
        session.expire(attempt)
        replay = session.scalars(
            select(PaymentAttempt).where(PaymentAttempt.external_event_id == external_event_id),
        ).first()
        if replay is None:
            raise
        return replay

    if succeeded:
        attempt.status = PaymentAttemptStatus.SUCCEEDED
        invoice = session.get(Invoice, attempt.invoice_id)
        if invoice is None:
            raise PaymentAttemptNotFoundError(attempt.invoice_id)
        invoice_service.mark_paid(session, invoice.id)
        order_service.mark_paid(session, invoice.order_id)
    else:
        attempt.status = PaymentAttemptStatus.FAILED
        attempt.failure_reason = failure_reason
    session.flush()
    return attempt
