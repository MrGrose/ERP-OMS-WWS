from sqlalchemy import select
from sqlalchemy.orm import Session

from erp_oms_wms.domains.audit import service as audit_service
from erp_oms_wms.domains.suppliers.errors import SupplierNotFoundError, SupplierProductNotFoundError
from erp_oms_wms.domains.suppliers.models import Supplier, SupplierProduct


def create_supplier(session: Session, *, code: str, name: str, actor: str) -> Supplier:
    supplier = Supplier(code=code, name=name, is_active=True)
    session.add(supplier)
    session.flush()
    audit_service.record(
        session,
        actor=actor,
        action="supplier.created",
        entity_type="supplier",
        entity_id=supplier.id,
        details=code,
    )
    return supplier


def list_suppliers(session: Session) -> list[Supplier]:
    return list(session.scalars(select(Supplier).order_by(Supplier.code)))


def get_supplier(session: Session, supplier_id: str) -> Supplier:
    supplier = session.get(Supplier, supplier_id)
    if supplier is None:
        raise SupplierNotFoundError(supplier_id)
    return supplier


def create_supplier_product(
    session: Session,
    supplier_id: str,
    sku: str,
    supplier_sku: str,
    purchase_price_cents: int,
    lead_time_days: int,
    actor: str,
) -> SupplierProduct:
    if session.get(Supplier, supplier_id) is None:
        raise SupplierNotFoundError(supplier_id)
    if purchase_price_cents < 0:
        raise ValueError("purchase_price_cents must be non-negative")
    row = SupplierProduct(
        supplier_id=supplier_id,
        sku=sku,
        supplier_sku=supplier_sku,
        purchase_price_cents=purchase_price_cents,
        lead_time_days=lead_time_days,
        is_active=True,
    )
    session.add(row)
    session.flush()
    audit_service.record(
        session,
        actor=actor,
        action="supplier_product.created",
        entity_type="supplier_product",
        entity_id=row.id,
        details=sku,
    )
    return row


def list_supplier_products(session: Session, supplier_id: str) -> list[SupplierProduct]:
    stmt = select(SupplierProduct).where(SupplierProduct.supplier_id == supplier_id)
    return list(session.scalars(stmt.order_by(SupplierProduct.sku)))


def get_supplier_product(session: Session, product_id: str) -> SupplierProduct:
    row = session.get(SupplierProduct, product_id)
    if row is None:
        raise SupplierProductNotFoundError(product_id)
    return row
