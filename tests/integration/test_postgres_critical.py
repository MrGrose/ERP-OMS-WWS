"""Критичные сценарии на PostgreSQL со схемой Alembic (head)."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

import erp_oms_wms.domains.invoices.service as invoice_service
import erp_oms_wms.domains.payments.service as payment_service
from erp_oms_wms.domains.inventory import service as inventory_service
from erp_oms_wms.domains.inventory.enums import ReservationStatus, StockMovementType
from erp_oms_wms.domains.inventory.models import InventoryLevel, Reservation, StockMovement
from erp_oms_wms.domains.invoices.enums import InvoiceStatus
from erp_oms_wms.domains.invoices.models import Invoice
from erp_oms_wms.domains.orders import service as order_service
from erp_oms_wms.domains.orders.enums import OrderStatus
from erp_oms_wms.domains.orders.errors import InvalidOrderTransitionError
from erp_oms_wms.domains.orders.models import Order
from erp_oms_wms.domains.payments.models import PaymentAttempt
from tests.helpers import seed_retail_price

pytestmark = pytest.mark.integration


def test_double_confirm_no_extra_movements(db_session: Session) -> None:
    inventory_service.apply_receipt(db_session, "wh-1", "SKU-DC", 5, "gr", "p1")
    seed_retail_price(db_session, "SKU-DC", 100)
    order = order_service.create_draft_order(
        db_session,
        customer_id=None,
        lines=[{"warehouse_id": "wh-1", "sku": "SKU-DC", "quantity": 1}],
    )
    order_service.confirm_order(db_session, order.id)
    with pytest.raises(InvalidOrderTransitionError):
        order_service.confirm_order(db_session, order.id)
    db_session.flush()
    moves = db_session.scalars(select(StockMovement)).all()
    reserves = db_session.scalars(select(Reservation)).all()
    assert len(moves) == 1
    assert moves[0].movement_type == StockMovementType.RECEIPT
    assert len(reserves) == 0


def test_partial_ship_and_overship_guard(db_session: Session) -> None:
    inventory_service.apply_receipt(db_session, "wh-1", "SKU-P", 10, "gr", "p1")
    seed_retail_price(db_session, "SKU-P")
    order = order_service.create_draft_order(
        db_session,
        customer_id=None,
        lines=[{"warehouse_id": "wh-1", "sku": "SKU-P", "quantity": 4}],
    )
    order_service.confirm_order(db_session, order.id)
    order_service.reserve_order(db_session, order.id)
    order_service.start_assembling(db_session, order.id)
    line_id = order.lines[0].id
    order_service.ship_order_line(db_session, order.id, line_id, 1)
    db_session.refresh(order)
    assert order.status == OrderStatus.ASSEMBLING
    assert order.lines[0].quantity_shipped == 1
    level = db_session.scalars(
        select(InventoryLevel).where(
            InventoryLevel.warehouse_id == "wh-1",
            InventoryLevel.sku == "SKU-P",
        ),
    ).one()
    assert level.on_hand == 9
    assert level.reserved == 3
    with pytest.raises(InvalidOrderTransitionError):
        order_service.ship_order_line(db_session, order.id, line_id, 10)
    order_service.ship_order_line(db_session, order.id, line_id, 3)
    reloaded = db_session.get(Order, order.id)
    assert reloaded is not None
    assert reloaded.status == OrderStatus.SHIPPED
    assert order.lines[0].quantity_shipped == 4
    level = db_session.scalars(
        select(InventoryLevel).where(
            InventoryLevel.warehouse_id == "wh-1",
            InventoryLevel.sku == "SKU-P",
        ),
    ).one()
    assert level.on_hand == 6
    assert level.reserved == 0


def test_webhook_idempotent_sequential(db_session: Session) -> None:
    inventory_service.apply_receipt(db_session, "wh-1", "SKU-P", 10, "gr", "p1")
    seed_retail_price(db_session, "SKU-P", 2500)
    order = order_service.create_draft_order(
        db_session,
        customer_id=None,
        lines=[{"warehouse_id": "wh-1", "sku": "SKU-P", "quantity": 2}],
    )
    order_service.confirm_order(db_session, order.id)
    order_service.reserve_order(db_session, order.id)
    invoice = invoice_service.issue_for_order(db_session, order.id, amount_cents=5000)
    attempt = payment_service.create_attempt(db_session, invoice.id)
    payment_service.apply_webhook(
        db_session,
        payment_attempt_id=attempt.id,
        external_event_id="evt-seq-1",
        succeeded=True,
    )
    again = payment_service.apply_webhook(
        db_session,
        payment_attempt_id=attempt.id,
        external_event_id="evt-seq-1",
        succeeded=True,
    )
    assert again.id == attempt.id
    paid_count = db_session.scalar(
        select(func.count())
        .select_from(PaymentAttempt)
        .where(
            PaymentAttempt.external_event_id == "evt-seq-1",
        ),
    )
    assert paid_count == 1
    paid_invoice = db_session.get(Invoice, invoice.id)
    assert paid_invoice is not None
    assert paid_invoice.status == InvoiceStatus.PAID
    db_session.refresh(order)
    assert order.status == OrderStatus.PAID


def test_invoice_expiry_idempotent(db_session: Session) -> None:
    inventory_service.apply_receipt(db_session, "wh-1", "SKU-E", 5, "gr", "p1")
    seed_retail_price(db_session, "SKU-E")
    order = order_service.create_draft_order(
        db_session,
        customer_id=None,
        lines=[{"warehouse_id": "wh-1", "sku": "SKU-E", "quantity": 2}],
    )
    order_service.confirm_order(db_session, order.id)
    order_service.reserve_order(db_session, order.id)
    invoice = invoice_service.issue_for_order(db_session, order.id, amount_cents=100)
    invoice.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.flush()
    assert invoice_service.expire_due_invoices(db_session) == 1
    assert invoice_service.expire_due_invoices(db_session) == 0
    db_session.refresh(order)
    assert order.status == OrderStatus.CANCELLED
    level = db_session.scalars(
        select(InventoryLevel).where(InventoryLevel.sku == "SKU-E"),
    ).one()
    assert level.reserved == 0
    released = db_session.scalars(
        select(Reservation).where(Reservation.order_id == order.id),
    ).all()
    assert len(released) == 1
    assert released[0].status == ReservationStatus.RELEASED
    release_moves = db_session.scalars(
        select(StockMovement).where(StockMovement.movement_type == StockMovementType.RELEASE),
    ).all()
    assert len(release_moves) == 1


def test_concurrent_webhook_same_event(pg_engine: Engine) -> None:
    from tests.integration.conftest import truncate_public_schema

    truncate_public_schema(pg_engine)
    factory = sessionmaker(bind=pg_engine, autoflush=False, autocommit=False)
    setup = factory()
    try:
        inventory_service.apply_receipt(setup, "wh-1", "SKU-CW", 10, "gr", "p1")
        seed_retail_price(setup, "SKU-CW", 1000)
        order = order_service.create_draft_order(
            setup,
            customer_id=None,
            lines=[{"warehouse_id": "wh-1", "sku": "SKU-CW", "quantity": 1}],
        )
        order_service.confirm_order(setup, order.id)
        order_service.reserve_order(setup, order.id)
        invoice = invoice_service.issue_for_order(setup, order.id, amount_cents=100)
        attempt = payment_service.create_attempt(setup, invoice.id)
        attempt_id = attempt.id
        order_id = order.id
        invoice_id = invoice.id
        setup.commit()
    finally:
        setup.close()

    def run_webhook() -> str:
        session = factory()
        try:
            payment_service.apply_webhook(
                session,
                payment_attempt_id=attempt_id,
                external_event_id="evt-concurrent",
                succeeded=True,
            )
            session.commit()
            return "ok"
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    outcomes: list[str] = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run_webhook) for _ in range(2)]
        for f in as_completed(futures):
            outcomes.append(f.result())

    assert outcomes == ["ok", "ok"]
    verify = factory()
    try:
        cnt = verify.scalar(
            select(func.count())
            .select_from(PaymentAttempt)
            .where(
                PaymentAttempt.external_event_id == "evt-concurrent",
            ),
        )
        assert cnt == 1
        inv = verify.get(Invoice, invoice_id)
        assert inv is not None and inv.status == InvoiceStatus.PAID
        ord_row = verify.get(Order, order_id)
        assert ord_row is not None and ord_row.status == OrderStatus.PAID
    finally:
        verify.close()
        truncate_public_schema(pg_engine)
