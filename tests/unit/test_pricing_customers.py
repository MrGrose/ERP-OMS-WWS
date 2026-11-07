from sqlalchemy.orm import Session

import erp_oms_wms.domains.customers.service as customer_service
import erp_oms_wms.domains.pricing.service as pricing_service
import erp_oms_wms.domains.reporting.service as reporting_service
from erp_oms_wms.domains.inventory import service as inventory_service
from erp_oms_wms.domains.orders import service as order_service
from erp_oms_wms.domains.pricing.enums import PriceList


def test_customer_price_list_on_confirm(db_session: Session) -> None:
    pricing_service.upsert_price(
        db_session, price_list=PriceList.RETAIL, sku="SKU-X", amount_cents=100
    )
    pricing_service.upsert_price(
        db_session, price_list=PriceList.WHOLESALE, sku="SKU-X", amount_cents=80
    )
    customer = customer_service.create_customer(
        db_session,
        name="Wholesale Co",
        email=None,
        price_list=PriceList.WHOLESALE,
        actor="test",
    )
    inventory_service.apply_receipt(db_session, "wh-1", "SKU-X", 5, "gr", "1")
    order = order_service.create_draft_order(
        db_session,
        customer_id=customer.id,
        lines=[{"warehouse_id": "wh-1", "sku": "SKU-X", "quantity": 1}],
    )
    order_service.confirm_order(db_session, order.id)
    db_session.refresh(order)
    assert order.lines[0].unit_price_cents == 80


def test_reporting_sales_after_ship(db_session: Session) -> None:
    seed_sku = "SKU-R"
    pricing_service.upsert_price(
        db_session, price_list=PriceList.RETAIL, sku=seed_sku, amount_cents=200
    )
    inventory_service.apply_receipt(db_session, "wh-1", seed_sku, 10, "gr", "r1")
    order = order_service.create_draft_order(
        db_session,
        customer_id=None,
        lines=[{"warehouse_id": "wh-1", "sku": seed_sku, "quantity": 2}],
    )
    order_service.confirm_order(db_session, order.id)
    order_service.reserve_order(db_session, order.id)
    order_service.start_assembling(db_session, order.id)
    order_service.ship_order(db_session, order.id)
    sales = reporting_service.sales_summary(db_session)
    row = next(item for item in sales if item["sku"] == seed_sku)
    assert row["revenue_cents"] == 400
