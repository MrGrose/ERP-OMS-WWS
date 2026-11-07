from sqlalchemy.orm import Session

from erp_oms_wms.domains.inventory import service as inventory_service
from erp_oms_wms.domains.orders import service as order_service
from erp_oms_wms.domains.orders.enums import OrderStatus
from erp_oms_wms.domains.orders.models import Order
from tests.helpers import seed_retail_price


def test_partial_line_ship_then_complete(db_session: Session) -> None:
    inventory_service.apply_receipt(db_session, "wh-1", "SKU-P", 10, "gr", "p")
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
    order_service.ship_order_line(db_session, order.id, line_id, 3)
    reloaded = db_session.get(Order, order.id)
    assert reloaded is not None
    assert reloaded.status == OrderStatus.SHIPPED
    assert order.lines[0].quantity_shipped == 4
