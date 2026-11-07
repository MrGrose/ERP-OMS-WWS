from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from erp_oms_wms.api import schemas
from erp_oms_wms.api.deps import get_db
from erp_oms_wms.api.rbac import UserRole, get_actor_id, require_roles
from erp_oms_wms.domains.suppliers import service as supplier_service
from erp_oms_wms.domains.suppliers.errors import SupplierNotFoundError, SupplierProductNotFoundError

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=list[schemas.SupplierOut])
def list_suppliers(session: Session = Depends(get_db)) -> list[schemas.SupplierOut]:
    return [schemas.SupplierOut.model_validate(s) for s in supplier_service.list_suppliers(session)]


@router.post("", response_model=schemas.SupplierOut, status_code=201)
def create_supplier(
    body: schemas.SupplierCreateIn,
    session: Session = Depends(get_db),
    actor: str = Depends(get_actor_id),
    _role: UserRole = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.ACCOUNTANT)),
) -> schemas.SupplierOut:
    supplier = supplier_service.create_supplier(
        session, code=body.code, name=body.name, actor=actor
    )
    return schemas.SupplierOut.model_validate(supplier)


@router.get("/supplier-products/{product_id}", response_model=schemas.SupplierProductOut)
def get_supplier_product(
    product_id: str, session: Session = Depends(get_db)
) -> schemas.SupplierProductOut:
    try:
        return schemas.SupplierProductOut.model_validate(
            supplier_service.get_supplier_product(session, product_id)
        )
    except SupplierProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{supplier_id}", response_model=schemas.SupplierOut)
def get_supplier(supplier_id: str, session: Session = Depends(get_db)) -> schemas.SupplierOut:
    try:
        return schemas.SupplierOut.model_validate(
            supplier_service.get_supplier(session, supplier_id)
        )
    except SupplierNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{supplier_id}/products", response_model=list[schemas.SupplierProductOut])
def list_supplier_products(
    supplier_id: str, session: Session = Depends(get_db)
) -> list[schemas.SupplierProductOut]:
    try:
        rows = supplier_service.list_supplier_products(session, supplier_id)
    except SupplierNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [schemas.SupplierProductOut.model_validate(r) for r in rows]


@router.post("/{supplier_id}/products", response_model=schemas.SupplierProductOut, status_code=201)
def create_supplier_product(
    supplier_id: str,
    body: schemas.SupplierProductCreateIn,
    session: Session = Depends(get_db),
    actor: str = Depends(get_actor_id),
    _role: UserRole = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
) -> schemas.SupplierProductOut:
    try:
        row = supplier_service.create_supplier_product(
            session,
            supplier_id=supplier_id,
            sku=body.sku,
            supplier_sku=body.supplier_sku,
            purchase_price_cents=body.purchase_price_cents,
            lead_time_days=body.lead_time_days,
            actor=actor,
        )
        return schemas.SupplierProductOut.model_validate(row)
    except SupplierNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
