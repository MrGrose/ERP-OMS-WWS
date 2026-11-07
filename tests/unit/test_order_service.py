import pytest
from sqlalchemy.orm import Session

from erp_oms_wms.domains.inventory import service as inventory_service
from erp_oms_wms.domains.orders import service as order_service
from erp_oms_wms.domains.orders.enums import OrderStatus
from erp_oms_wms.domains.orders.errors import InvalidOrderTransitionError
from tests.helpers import seed_retail_price


def _line(sku: str = "SKU-1", qty: int = 2) -> dict[str, object]:
    return {"warehouse_id": "wh-1", "sku": sku, "quantity": qty}


def test_order_happy_path(db_session: Session) -> None:
    inventory_service.apply_receipt(db_session, "wh-1", "SKU-1", 10, "gr", "1")
    seed_retail_price(db_session, "SKU-1", 500)
    order = order_service.create_draft_order(db_session, customer_id=None, lines=[_line()])
    assert order.status == OrderStatus.DRAFT
    order_service.confirm_order(db_session, order.id)
    order_service.reserve_order(db_session, order.id)
    db_session.refresh(order)
    assert order.status == OrderStatus.RESERVED
    assert order.lines[0].reservation_id is not None
    order_service.start_assembling(db_session, order.id)
    order_service.ship_order(db_session, order.id)
    db_session.refresh(order)
    assert order.status == OrderStatus.SHIPPED


def test_cannot_reserve_from_draft(db_session: Session) -> None:
    order = order_service.create_draft_order(db_session, customer_id=None, lines=[_line()])
    with pytest.raises(InvalidOrderTransitionError):
        order_service.reserve_order(db_session, order.id)


def test_cancel_releases_reservation(db_session: Session) -> None:
    inventory_service.apply_receipt(db_session, "wh-1", "SKU-1", 5, "gr", "2")
    seed_retail_price(db_session, "SKU-1")
    order = order_service.create_draft_order(db_session, customer_id=None, lines=[_line(qty=2)])
    order_service.confirm_order(db_session, order.id)
    order_service.reserve_order(db_session, order.id)
    order_service.cancel_order(db_session, order.id)
    db_session.refresh(order)
    assert order.status == OrderStatus.CANCELLED
