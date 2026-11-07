import enum
from collections.abc import Callable

from fastapi import Depends, Header, HTTPException


class UserRole(enum.StrEnum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    WAREHOUSE_OPERATOR = "WarehouseOperator"
    ACCOUNTANT = "Accountant"


def get_actor_id(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> str:
    return x_user_id or "system"


def get_current_role(
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
) -> UserRole:
    if x_user_role is None:
        return UserRole.ADMIN
    for role in UserRole:
        if role.value == x_user_role:
            return role
    raise HTTPException(status_code=403, detail="unknown role")


def require_roles(*allowed: UserRole) -> Callable[..., UserRole]:
    def _dependency(role: UserRole = Depends(get_current_role)) -> UserRole:
        if role not in allowed:
            raise HTTPException(status_code=403, detail="insufficient role")
        return role

    return _dependency


ROLE_PERMISSIONS: dict[UserRole, frozenset[str]] = {
    UserRole.ADMIN: frozenset(
        {
            "catalog.read",
            "catalog.write",
            "inventory.read",
            "inventory.adjust",
            "orders.read",
            "orders.manage",
            "payments.read",
            "finance.read",
        },
    ),
    UserRole.MANAGER: frozenset(
        {
            "catalog.read",
            "catalog.write",
            "inventory.read",
            "orders.read",
            "orders.manage",
            "payments.read",
            "finance.read",
        },
    ),
    UserRole.WAREHOUSE_OPERATOR: frozenset(
        {"catalog.read", "inventory.read", "inventory.adjust", "orders.read", "orders.manage"},
    ),
    UserRole.ACCOUNTANT: frozenset(
        {"catalog.read", "inventory.read", "orders.read", "payments.read", "finance.read"},
    ),
}


def require_permission(permission: str) -> Callable[..., UserRole]:
    def _dependency(role: UserRole = Depends(get_current_role)) -> UserRole:
        allowed = ROLE_PERMISSIONS.get(role, frozenset())
        if permission not in allowed:
            raise HTTPException(status_code=403, detail=f"missing permission: {permission}")
        return role

    return _dependency
