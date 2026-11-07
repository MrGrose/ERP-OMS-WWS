from datetime import UTC, datetime

from sqlalchemy.orm import Session

from erp_oms_wms.domains.audit import service as audit_service
from erp_oms_wms.domains.inventory import service as inventory_service
from erp_oms_wms.domains.transfers.enums import WarehouseTransferStatus
from erp_oms_wms.domains.transfers.errors import (
    InvalidTransferTransitionError,
    TransferNotFoundError,
)
from erp_oms_wms.domains.transfers.models import WarehouseTransfer


def create_transfer(
    session: Session,
    *,
    from_warehouse_id: str,
    to_warehouse_id: str,
    sku: str,
    quantity: int,
    actor: str,
) -> WarehouseTransfer:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    if from_warehouse_id == to_warehouse_id:
        raise ValueError("source and destination warehouse must differ")
    transfer = WarehouseTransfer(
        from_warehouse_id=from_warehouse_id,
        to_warehouse_id=to_warehouse_id,
        sku=sku,
        quantity=quantity,
        status=WarehouseTransferStatus.DRAFT,
    )
    session.add(transfer)
    session.flush()
    audit_service.record(
        session,
        actor=actor,
        action="transfer.created",
        entity_type="warehouse_transfer",
        entity_id=transfer.id,
    )
    return transfer


def complete_transfer(session: Session, transfer_id: str, *, actor: str) -> WarehouseTransfer:
    transfer = session.get(WarehouseTransfer, transfer_id)
    if transfer is None:
        raise TransferNotFoundError(transfer_id)
    if transfer.status != WarehouseTransferStatus.DRAFT:
        raise InvalidTransferTransitionError(
            f"transfer {transfer_id} status {transfer.status.value}"
        )
    inventory_service.transfer_stock(
        session,
        from_warehouse_id=transfer.from_warehouse_id,
        to_warehouse_id=transfer.to_warehouse_id,
        sku=transfer.sku,
        quantity=transfer.quantity,
        reference_type="warehouse_transfer",
        reference_id=transfer.id,
    )
    transfer.status = WarehouseTransferStatus.COMPLETED
    transfer.completed_at = datetime.now(UTC)
    session.flush()
    audit_service.record(
        session,
        actor=actor,
        action="transfer.completed",
        entity_type="warehouse_transfer",
        entity_id=transfer.id,
    )
    return transfer


def cancel_transfer(session: Session, transfer_id: str, *, actor: str) -> WarehouseTransfer:
    transfer = session.get(WarehouseTransfer, transfer_id)
    if transfer is None:
        raise TransferNotFoundError(transfer_id)
    if transfer.status != WarehouseTransferStatus.DRAFT:
        raise InvalidTransferTransitionError(
            f"transfer {transfer_id} status {transfer.status.value}"
        )
    transfer.status = WarehouseTransferStatus.CANCELLED
    session.flush()
    audit_service.record(
        session,
        actor=actor,
        action="transfer.cancelled",
        entity_type="warehouse_transfer",
        entity_id=transfer.id,
    )
    return transfer
