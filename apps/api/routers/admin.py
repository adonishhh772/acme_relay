from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from auth.dependencies import CurrentUser, require_permission
from auth.keycloak_admin import (
    KeycloakAdminError,
    get_keycloak_admin_client,
    map_keycloak_admin_error,
)
from auth.rbac import PERMISSIONS, TOOL_PERMISSION
from schemas.enums import Role
from support.db import acquire

router = APIRouter(prefix="/api/admin", tags=["admin"])

VALID_APP_ROLES = {role.value for role in Role}


class UpdateUserBody(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class RolePermissionsBody(BaseModel):
    permission_keys: list[str] = Field(default_factory=list)


@router.get("/overview")
async def admin_overview(
    user: Annotated[CurrentUser, Depends(require_permission("manage_users"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        users = await connection.fetchval("SELECT count(*) FROM users")
        active_users = await connection.fetchval(
            "SELECT count(*) FROM users WHERE is_active"
        )
        roles = await connection.fetchval(
            "SELECT count(*) FROM rbac_roles WHERE is_active"
        )
        permissions = await connection.fetchval("SELECT count(*) FROM permissions")
        orgs = await connection.fetchval(
            "SELECT count(*) FROM organizations WHERE is_active"
        )
    return {
        "users": users,
        "active_users": active_users,
        "roles": roles,
        "permissions": permissions,
        "organizations": orgs,
    }


@router.get("/users")
async def list_users(
    user: Annotated[CurrentUser, Depends(require_permission("manage_users"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT u.id::text AS id, u.email, u.display_name, u.role::text AS role,
                   u.is_active, u.keycloak_sub, o.slug AS organization_slug,
                   o.display_name AS organization_name
            FROM users u
            LEFT JOIN organizations o ON o.id = u.organization_id
            ORDER BY u.display_name
            """
        )

    items: list[dict[str, Any]] = []
    client = get_keycloak_admin_client()
    for row in rows:
        item = dict(row)
        keycloak_sub = item.get("keycloak_sub")
        item["totp_configured"] = False
        item["mfa_setup_pending"] = False
        item["required_actions"] = []
        if keycloak_sub:
            try:
                summary = await client.sync_totp_state(str(keycloak_sub))
                item["totp_configured"] = summary.totp_configured
                item["required_actions"] = summary.required_actions
                item["mfa_setup_pending"] = "CONFIGURE_TOTP" in summary.required_actions
            except KeycloakAdminError:
                item["mfa_status_error"] = True
        items.append(item)
    return {"items": items}


@router.post("/users/{keycloak_sub}/require-2fa")
async def require_user_2fa(
    keycloak_sub: str,
    user: Annotated[CurrentUser, Depends(require_permission("manage_users"))],
) -> dict[str, Any]:
    client = get_keycloak_admin_client()
    try:
        summary = await client.require_totp_setup(keycloak_sub)
    except KeycloakAdminError as exc:
        raise map_keycloak_admin_error(exc) from exc
    return {
        "user_id": summary.id,
        "totp_configured": summary.totp_configured,
        "mfa_setup_pending": "CONFIGURE_TOTP" in summary.required_actions,
        "required_actions": summary.required_actions,
        "message": f"MFA required for next sign-in (actor={user.username}).",
    }


@router.post("/users/{keycloak_sub}/disable-2fa")
async def disable_user_2fa(
    keycloak_sub: str,
    user: Annotated[CurrentUser, Depends(require_permission("manage_users"))],
) -> dict[str, Any]:
    client = get_keycloak_admin_client()
    try:
        summary = await client.disable_totp(keycloak_sub)
    except KeycloakAdminError as exc:
        raise map_keycloak_admin_error(exc) from exc
    return {
        "user_id": summary.id,
        "totp_configured": summary.totp_configured,
        "mfa_setup_pending": "CONFIGURE_TOTP" in summary.required_actions,
        "required_actions": summary.required_actions,
        "message": f"MFA disabled for user (actor={user.username}).",
    }


@router.post("/users/{keycloak_sub}/sync-2fa")
async def sync_user_2fa(
    keycloak_sub: str,
    user: Annotated[CurrentUser, Depends(require_permission("manage_users"))],
) -> dict[str, Any]:
    _ = user
    client = get_keycloak_admin_client()
    try:
        summary = await client.sync_totp_state(keycloak_sub)
    except KeycloakAdminError as exc:
        raise map_keycloak_admin_error(exc) from exc
    return {
        "user_id": summary.id,
        "totp_configured": summary.totp_configured,
        "mfa_setup_pending": "CONFIGURE_TOTP" in summary.required_actions,
        "required_actions": summary.required_actions,
    }


@router.patch("/users/{email}")
async def update_user(
    email: str,
    body: UpdateUserBody,
    user: Annotated[CurrentUser, Depends(require_permission("manage_users"))],
) -> dict[str, Any]:
    _ = user
    if body.role is None and body.is_active is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")
    if body.role is not None and body.role not in VALID_APP_ROLES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Invalid role. Expected one of: {sorted(VALID_APP_ROLES)}",
        )
    async with acquire() as connection:
        existing = await connection.fetchrow(
            "SELECT email FROM users WHERE email = $1", email
        )
        if existing is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        if body.role is not None:
            await connection.execute(
                "UPDATE users SET role = $1::app_role, updated_at = now() WHERE email = $2",
                body.role,
                email,
            )
        if body.is_active is not None:
            await connection.execute(
                "UPDATE users SET is_active = $1, updated_at = now() WHERE email = $2",
                body.is_active,
                email,
            )
        row = await connection.fetchrow(
            """
            SELECT u.id::text AS id, u.email, u.display_name, u.role::text AS role,
                   u.is_active, o.slug AS organization_slug
            FROM users u
            LEFT JOIN organizations o ON o.id = u.organization_id
            WHERE u.email = $1
            """,
            email,
        )
    return {"item": dict(row) if row else None}


@router.get("/roles")
async def list_roles(
    user: Annotated[CurrentUser, Depends(require_permission("manage_roles"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT r.id::text AS id, r.slug, r.name, r.description, r.is_system,
                   r.keycloak_role_name, r.is_active,
                   coalesce(
                     array_agg(p.key ORDER BY p.key) FILTER (WHERE p.key IS NOT NULL),
                     '{}'
                   ) AS permission_keys
            FROM rbac_roles r
            LEFT JOIN role_permissions rp ON rp.role_id = r.id
            LEFT JOIN permissions p ON p.id = rp.permission_id
            WHERE r.is_active
            GROUP BY r.id
            ORDER BY r.slug
            """
        )
    items = []
    for row in rows:
        item = dict(row)
        keys = item.pop("permission_keys") or []
        item["permission_keys"] = list(keys)
        items.append(item)
    return {"items": items}


@router.get("/rbac-matrix")
async def rbac_matrix(
    user: Annotated[CurrentUser, Depends(require_permission("manage_roles"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        permissions = await connection.fetch(
            """
            SELECT key, description, category
            FROM permissions
            ORDER BY category, key
            """
        )
        roles = await connection.fetch(
            """
            SELECT r.slug, r.name, r.keycloak_role_name, r.is_system,
                   coalesce(
                     array_agg(p.key ORDER BY p.key) FILTER (WHERE p.key IS NOT NULL),
                     '{}'
                   ) AS permission_keys
            FROM rbac_roles r
            LEFT JOIN role_permissions rp ON rp.role_id = r.id
            LEFT JOIN permissions p ON p.id = rp.permission_id
            WHERE r.is_active
            GROUP BY r.id
            ORDER BY r.slug
            """
        )
    role_items = []
    for row in roles:
        item = dict(row)
        item["permission_keys"] = list(item.pop("permission_keys") or [])
        role_items.append(item)
    return {
        "permissions": [dict(row) for row in permissions],
        "roles": role_items,
        "runtime_permissions": {
            key: sorted(role.value for role in allowed)
            for key, allowed in PERMISSIONS.items()
        },
        "tool_permissions": TOOL_PERMISSION,
    }


@router.put("/roles/{slug}/permissions")
async def set_role_permissions(
    slug: str,
    body: RolePermissionsBody,
    user: Annotated[CurrentUser, Depends(require_permission("manage_roles"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        role = await connection.fetchrow(
            "SELECT id, slug, is_system FROM rbac_roles WHERE slug = $1 AND is_active",
            slug,
        )
        if role is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
        valid = await connection.fetch(
            "SELECT key FROM permissions WHERE key = ANY($1::text[])",
            body.permission_keys,
        )
        valid_keys = {row["key"] for row in valid}
        unknown = sorted(set(body.permission_keys) - valid_keys)
        if unknown:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Unknown permissions: {unknown}",
            )
        async with connection.transaction():
            await connection.execute(
                "DELETE FROM role_permissions WHERE role_id = $1", role["id"]
            )
            for key in sorted(valid_keys):
                await connection.execute(
                    """
                    INSERT INTO role_permissions (role_id, permission_id)
                    SELECT $1, id FROM permissions WHERE key = $2
                    ON CONFLICT DO NOTHING
                    """,
                    role["id"],
                    key,
                )
        keys = await connection.fetch(
            """
            SELECT p.key
            FROM role_permissions rp
            JOIN permissions p ON p.id = rp.permission_id
            WHERE rp.role_id = $1
            ORDER BY p.key
            """,
            role["id"],
        )
    return {
        "slug": slug,
        "permission_keys": [row["key"] for row in keys],
        "note": (
            "Catalog updated. Agent runtime still enforces auth/rbac.py for tool calls; "
            "keep Keycloak realm roles aligned with these slugs."
        ),
    }


@router.get("/organizations")
async def list_organizations(
    user: Annotated[CurrentUser, Depends(require_permission("manage_organizations"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT o.slug, o.display_name, o.is_active, o.created_at,
                   (SELECT count(*) FROM users u WHERE u.organization_id = o.id) AS user_count,
                   (SELECT count(*) FROM customers c WHERE c.organization_id = o.id) AS customer_count
            FROM organizations o
            ORDER BY o.display_name
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
