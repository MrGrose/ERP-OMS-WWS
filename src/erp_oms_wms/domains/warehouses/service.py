from sqlalchemy import select
from sqlalchemy.orm import Session

from erp_oms_wms.domains.warehouses.errors import WarehouseNotFoundError
from erp_oms_wms.domains.warehouses.models import Warehouse


def create_warehouse(session: Session, *, warehouse_id: str, name: str) -> Warehouse:
    if session.get(Warehouse, warehouse_id) is not None:
        raise ValueError(f"warehouse {warehouse_id} already exists")
    wh = Warehouse(id=warehouse_id, name=name, is_active=True)
    session.add(wh)
    session.flush()
    return wh


def list_warehouses(session: Session) -> list[Warehouse]:
    return list(session.scalars(select(Warehouse).order_by(Warehouse.id)))


def get_warehouse(session: Session, warehouse_id: str) -> Warehouse:
    wh = session.get(Warehouse, warehouse_id)
    if wh is None:
        raise WarehouseNotFoundError(warehouse_id)
    return wh
