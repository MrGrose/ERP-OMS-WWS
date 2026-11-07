import pytest
from sqlalchemy.orm import Session

import erp_oms_wms.domains.customers.service as customer_service
from erp_oms_wms.domains.orders import service as order_service
from erp_oms_wms.domains.orders.errors import InvalidOrderTransitionError
from erp_oms_wms.domains.pricing.enums import PriceList
from tests.helpers import seed_retail_price


def test_inactive_customer_blocks_confirm(db_session: Session) -> None:
    seed_retail_price(db_session, "SKU-INACT", 100)
    customer = customer_service.create_customer(
        db_session,
        name="Inactive",
        email=None,
        price_list=PriceList.RETAIL,
        actor="test",
    )
    customer.is_active = False
    db_session.flush()
    order = order_service.create_draft_order(
        db_session,
        customer_id=customer.id,
        lines=[{"warehouse_id": "wh-1", "sku": "SKU-INACT", "quantity": 1}],
    )
    with pytest.raises(InvalidOrderTransitionError, match="inactive"):
        order_service.confirm_order(db_session, order.id)


def test_double_confirm_rejected(db_session: Session) -> None:
    seed_retail_price(db_session, "SKU-DC", 100)
    order = order_service.create_draft_order(
        db_session,
        customer_id=None,
        lines=[{"warehouse_id": "wh-1", "sku": "SKU-DC", "quantity": 1}],
    )
    order_service.confirm_order(db_session, order.id)
    with pytest.raises(InvalidOrderTransitionError):
        order_service.confirm_order(db_session, order.id)
