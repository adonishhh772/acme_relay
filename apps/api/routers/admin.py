from typing import Annotated, Any

from fastapi import APIRouter, Depends

from auth.dependencies import CurrentUser, require_permission
from support.db import acquire

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users")
async def list_users(
    user: Annotated[CurrentUser, Depends(require_permission("manage_users"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT u.email, u.display_name, u.role::text AS role, u.is_active,
                   o.slug AS organization_slug
            FROM users u
            LEFT JOIN organizations o ON o.id = u.organization_id
            ORDER BY u.display_name
            """
        )
    return {"items": [dict(row) for row in rows]}


@router.get("/roles")
async def list_roles(
    user: Annotated[CurrentUser, Depends(require_permission("manage_roles"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT slug, name, description, is_system, keycloak_role_name, is_active
            FROM rbac_roles
            WHERE is_active
            ORDER BY slug
            """
        )
    return {"items": [dict(row) for row in rows]}


@router.get("/organizations")
async def list_organizations(
    user: Annotated[CurrentUser, Depends(require_permission("manage_organizations"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT slug, display_name, is_active, created_at
            FROM organizations
            ORDER BY display_name
            """
        )
    return {"items": [dict(row) for row in rows]}


@router.get("/permissions")
async def list_permissions(
    user: Annotated[CurrentUser, Depends(require_permission("manage_roles"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT key, description, category
            FROM permissions
            ORDER BY category, key
            """
        )
    return {"items": [dict(row) for row in rows]}
