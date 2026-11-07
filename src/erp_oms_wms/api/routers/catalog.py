from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from erp_oms_wms.api import schemas
from erp_oms_wms.api.deps import get_db
from erp_oms_wms.api.rbac import UserRole, get_actor_id, require_roles
from erp_oms_wms.domains.catalog import service as catalog_service
from erp_oms_wms.domains.catalog.errors import ProductNotFoundError

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/products", response_model=list[schemas.ProductOut])
def list_products(session: Session = Depends(get_db)) -> list[schemas.ProductOut]:
    return [schemas.ProductOut.model_validate(p) for p in catalog_service.list_products(session)]


@router.post("/products", response_model=schemas.ProductOut, status_code=201)
def create_product(
    body: schemas.ProductCreateIn,
    session: Session = Depends(get_db),
    actor: str = Depends(get_actor_id),
    _role: UserRole = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
) -> schemas.ProductOut:
    try:
        product = catalog_service.create_product(session, sku=body.sku, name=body.name, actor=actor)
        return schemas.ProductOut.model_validate(product)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/products/{sku}", response_model=schemas.ProductOut)
def get_product(sku: str, session: Session = Depends(get_db)) -> schemas.ProductOut:
    try:
        return schemas.ProductOut.model_validate(catalog_service.get_product(session, sku))
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
