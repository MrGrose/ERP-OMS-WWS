from sqlalchemy import select
from sqlalchemy.orm import Session

from erp_oms_wms.domains.customers.errors import CustomerInactiveError, CustomerNotFoundError
from erp_oms_wms.domains.customers.models import Customer
from erp_oms_wms.domains.pricing.enums import PriceList
from erp_oms_wms.domains.pricing.errors import PriceNotFoundError
from erp_oms_wms.domains.pricing.models import ProductPrice


def upsert_price(
    session: Session,
    price_list: PriceList,
    sku: str,
    amount_cents: int,
    currency: str = "RUB",
) -> ProductPrice:
    if amount_cents < 0:
        raise ValueError("amount_cents must be non-negative")
    row = session.get(ProductPrice, (price_list, sku))
    if row is None:
        row = ProductPrice(
            price_list=price_list,
            sku=sku,
            amount_cents=amount_cents,
            currency=currency,
        )
        session.add(row)
    else:
        row.amount_cents = amount_cents
        row.currency = currency
    session.flush()
    return row


def list_prices(session: Session, *, price_list: PriceList | None = None) -> list[ProductPrice]:
    stmt = select(ProductPrice).order_by(ProductPrice.sku)
    if price_list is not None:
        stmt = stmt.where(ProductPrice.price_list == price_list)
    return list(session.scalars(stmt))


def resolve_unit_price_cents(
    session: Session,
    sku: str,
    customer_id: str | None,
) -> int:
    price_list = PriceList.RETAIL
    if customer_id is not None:
        customer = session.get(Customer, customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)
        if not customer.is_active:
            raise CustomerInactiveError(customer_id)
        price_list = customer.price_list
    row = session.get(ProductPrice, (price_list, sku))
    if row is None:
        raise PriceNotFoundError(price_list.value, sku)
    return row.amount_cents
