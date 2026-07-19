from typing import Annotated, Any

from fastapi import APIRouter, Depends

from auth.dependencies import CurrentUser, get_current_user
from auth.rbac import PERMISSIONS
from config import Settings, get_settings
from support.db import acquire

router = APIRouter(prefix="/api/account", tags=["account"])


@router.get("/me")
async def get_me(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    role_values = sorted(role.value for role in user.roles)
    permissions = sorted(
        key for key, allowed in PERMISSIONS.items() if user.roles & allowed
    )
    org_name = "Acme Operations"
    async with acquire() as connection:
        org = await connection.fetchrow(
            "SELECT slug, display_name FROM organizations WHERE slug = 'acme-ops' LIMIT 1"
        )
        if org:
            org_name = org["display_name"]
    return {
        "sub": user.sub,
        "username": user.username,
        "email": user.email,
        "roles": role_values,
        "permissions": permissions,
        "organization": org_name,
        "keycloak_account_url": (
            f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/account"
        ),
    }


@router.get("/security")
async def security_info(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    _ = user
    return {
        "totp_supported": True,
        "account_console_url": (
            f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/account"
        ),
        "hint": "Configure TOTP in the Keycloak account console.",
    }
