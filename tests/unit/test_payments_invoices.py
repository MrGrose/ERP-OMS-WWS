from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

import erp_oms_wms.domains.invoices.service as invoice_service
import erp_oms_wms.domains.payments.service as payment_service
from erp_oms_wms.domains.inventory import service as inventory_service
from erp_oms_wms.domains.inventory.models import InventoryLevel
from erp_oms_wms.domains.invoices.enums import InvoiceStatus
from erp_oms_wms.domains.invoices.models import Invoice
from erp_oms_wms.domains.orders import service as order_service
from erp_oms_wms.domains.orders.enums import OrderStatus
from erp_oms_wms.domains.orders.models import Order
from erp_oms_wms.domains.payments.enums import PaymentAttemptStatus
from tests.helpers import seed_retail_price


def _reserved_order(db_session: Session) -> Order:
    inventory_service.apply_receipt(db_session, "wh-1", "SKU-P", 10, "gr", "p1")
    seed_retail_price(db_session, "SKU-P", 2500)
    order = order_service.create_draft_order(
        db_session,
        customer_id=None,
        lines=[{"warehouse_id": "wh-1", "sku": "SKU-P", "quantity": 2}],
    )
    order_service.confirm_order(db_session, order.id)
    order_service.reserve_order(db_session, order.id)
    return order


def test_payment_success_marks_order_paid(db_session: Session) -> None:
    order = _reserved_order(db_session)
    invoice = invoice_service.issue_for_order(db_session, order.id, amount_cents=5000)
    attempt = payment_service.create_attempt(db_session, invoice.id)
    payment_service.apply_webhook(
        db_session,
        payment_attempt_id=attempt.id,
        external_event_id="evt-1",
        succeeded=True,
    )
    db_session.refresh(order)
    assert order.status == OrderStatus.PAID
    inv = db_session.get(Invoice, invoice.id)
    assert inv is not None and inv.status == InvoiceStatus.PAID
    assert attempt.status == PaymentAttemptStatus.SUCCEEDED


def test_webhook_idempotent(db_session: Session) -> None:
    order = _reserved_order(db_session)
    invoice = invoice_service.issue_for_order(db_session, order.id, amount_cents=100)
    attempt = payment_service.create_attempt(db_session, invoice.id)
    payment_service.apply_webhook(
        db_session,
        payment_attempt_id=attempt.id,
        external_event_id="evt-dup",
        succeeded=True,
    )
    again = payment_service.apply_webhook(
        db_session,
        payment_attempt_id=attempt.id,
        external_event_id="evt-dup",
        succeeded=True,
    )
    assert again.id == attempt.id
    assert again.status == PaymentAttemptStatus.SUCCEEDED


def test_invoice_expiry_releases_stock(db_session: Session) -> None:
    order = _reserved_order(db_session)
    invoice = invoice_service.issue_for_order(db_session, order.id, amount_cents=100)
    invoice.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.flush()
    assert invoice_service.expire_due_invoices(db_session) == 1
    db_session.refresh(order)
    assert order.status == OrderStatus.CANCELLED
    level = db_session.scalars(select(InventoryLevel).where(InventoryLevel.sku == "SKU-P")).one()
    assert level.reserved == 0
    assert level.available == level.on_hand
