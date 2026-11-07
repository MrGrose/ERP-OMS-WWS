from sqlalchemy import select
from sqlalchemy.orm import Session

from erp_oms_wms.domains.audit import service as audit_service
from erp_oms_wms.domains.catalog.errors import ProductNotFoundError
from erp_oms_wms.domains.catalog.models import Product


def create_product(session: Session, *, sku: str, name: str, actor: str) -> Product:
    if session.get(Product, sku) is not None:
        raise ValueError(f"product {sku} already exists")
    product = Product(sku=sku, name=name, is_active=True)
    session.add(product)
    session.flush()
    audit_service.record(
        session,
        actor=actor,
        action="product.created",
        entity_type="product",
        entity_id=sku,
    )
    return product


def list_products(session: Session) -> list[Product]:
    return list(session.scalars(select(Product).order_by(Product.sku)))


def get_product(session: Session, sku: str) -> Product:
    product = session.get(Product, sku)
    if product is None:
        raise ProductNotFoundError(sku)
    return product
