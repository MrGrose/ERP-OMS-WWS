from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from erp_oms_wms.domains.invoices.enums import InvoiceStatus
from erp_oms_wms.domains.invoices.errors import (
    InvalidInvoiceTransitionError,
    InvoiceNotFoundError,
)
from erp_oms_wms.domains.invoices.models import Invoice
from erp_oms_wms.domains.orders import service as order_service
from erp_oms_wms.domains.orders.enums import OrderStatus


# Выставляет счет для заказа в RESERVED (-> PENDING_PAYMENT).
def issue_for_order(
    session: Session,
    order_id: str,
    amount_cents: int | None = None,
    currency: str = "RUB",
    payment_deadline_hours: int = 24,
) -> Invoice:
    order = order_service._load_order(session, order_id)  # noqa: SLF001
    if order.status != OrderStatus.RESERVED:
        raise InvalidInvoiceTransitionError("Счет только для заказа в RESERVED")
    total = amount_cents
    if total is None:
        total = order_service.compute_order_total_cents(order)
    expires_at = datetime.now(UTC) + timedelta(hours=payment_deadline_hours)
    invoice = Invoice(
        order_id=order_id,
        amount_cents=total,
        currency=currency,
        status=InvoiceStatus.PENDING_PAYMENT,
        expires_at=expires_at,
    )
    session.add(invoice)
    session.flush()
    return invoice


def mark_paid(session: Session, invoice_id: str) -> Invoice:
    invoice = _get_invoice(session, invoice_id)
    if invoice.status != InvoiceStatus.PENDING_PAYMENT:
        raise InvalidInvoiceTransitionError(f"invoice {invoice_id} not pending")
    invoice.status = InvoiceStatus.PAID
    session.flush()
    return invoice


# Истк срок оплаты: счет EXPIRED, снятие резервов (через cancel заказа).
def expire_invoice(session: Session, invoice_id: str) -> Invoice:
    invoice = _get_invoice(session, invoice_id)
    if invoice.status != InvoiceStatus.PENDING_PAYMENT:
        return invoice
    invoice.status = InvoiceStatus.EXPIRED
    order = order_service._load_order(session, invoice.order_id)  # noqa: SLF001
    if order.status == OrderStatus.RESERVED:
        order_service.cancel_order(session, invoice.order_id)
    session.flush()
    return invoice


def expire_due_invoices(session: Session, *, now: datetime | None = None) -> int:
    moment = now or datetime.now(UTC)
    stmt = select(Invoice).where(
        Invoice.status == InvoiceStatus.PENDING_PAYMENT,
        Invoice.expires_at.is_not(None),
        Invoice.expires_at < moment,
    )
    count = 0
    for invoice in session.scalars(stmt):
        expire_invoice(session, invoice.id)
        count += 1
    return count


def _get_invoice(session: Session, invoice_id: str) -> Invoice:
    invoice = session.get(Invoice, invoice_id)
    if invoice is None:
        raise InvoiceNotFoundError(invoice_id)
    return invoice
