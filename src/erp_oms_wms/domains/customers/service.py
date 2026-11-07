from sqlalchemy import select
from sqlalchemy.orm import Session

from erp_oms_wms.domains.audit import service as audit_service
from erp_oms_wms.domains.customers.errors import CustomerNotFoundError
from erp_oms_wms.domains.customers.models import Customer
from erp_oms_wms.domains.pricing.enums import PriceList


def create_customer(
    session: Session,
    *,
    name: str,
    email: str | None,
    price_list: PriceList,
    actor: str,
) -> Customer:
    customer = Customer(name=name, email=email, price_list=price_list, is_active=True)
    session.add(customer)
    session.flush()
    audit_service.record(
        session,
        actor=actor,
        action="customer.created",
        entity_type="customer",
        entity_id=customer.id,
    )
    return customer


def list_customers(session: Session) -> list[Customer]:
    return list(session.scalars(select(Customer).order_by(Customer.name)))


def get_customer(session: Session, customer_id: str) -> Customer:
    customer = session.get(Customer, customer_id)
    if customer is None:
        raise CustomerNotFoundError(customer_id)
    return customer
