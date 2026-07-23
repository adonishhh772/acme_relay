"""Signed-in account profile, password, and MFA status — Keycloak-backed, Relay UI."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from auth.dependencies import CurrentUser, get_current_user
from auth.keycloak_admin import (
    KeycloakAdminError,
    get_keycloak_admin_client,
    map_keycloak_admin_error,
)
from auth.rbac import PERMISSIONS, TOOL_PERMISSION
from config import Settings, get_settings
from support.db import acquire

logger = logging.getLogger("relay.account")

router = APIRouter(prefix="/api/account", tags=["account"])

MIN_PASSWORD_LENGTH = 8


class UpdateProfileBody(BaseModel):
    email: str | None = Field(default=None, max_length=254)
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)


class ChangePasswordBody(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=MIN_PASSWORD_LENGTH)


def _permissions_payload(user: CurrentUser) -> dict[str, Any]:
    role_values = sorted(role.value for role in user.roles)
    permissions = sorted(
        key for key, allowed in PERMISSIONS.items() if user.roles & allowed
    )
    by_category: dict[str, list[str]] = {}
    for key in permissions:
        category = "general"
        if key.startswith("manage_") or key in {"view_audit", "run_evals"}:
            category = "admin"
        elif key.startswith("mcp_"):
            category = "mcp"
        elif "knowledge" in key:
            category = "knowledge"
        elif "issue" in key or key in {"summarize_issues", "update_issue"}:
            category = "issues"
        elif "action" in key or key == "recommend_action":
            category = "actions"
        elif key in {"read_customer"}:
            category = "customers"
        elif key in {"run_skill"}:
            category = "agent"
        elif key == "manage_tasks":
            category = "tasks"
        by_category.setdefault(category, []).append(key)

    allowed_tools = sorted(
        tool
        for tool, permission in TOOL_PERMISSION.items()
        if permission in set(permissions)
        or (permission and any(user.roles & PERMISSIONS.get(permission, set())))
    )
    return {
        "roles": role_values,
        "permissions": permissions,
        "permissions_by_category": by_category,
        "allowed_tools": allowed_tools,
    }


async def _organization_payload() -> dict[str, str]:
    org_name = "Acme Operations"
    org_slug = "acme-ops"
    async with acquire() as connection:
        org = await connection.fetchrow(
            "SELECT slug, display_name FROM organizations WHERE slug = 'acme-ops' LIMIT 1"
        )
        if org:
            org_name = org["display_name"]
            org_slug = org["slug"]
    return {"organization": org_name, "organization_slug": org_slug}


@router.get("/me")
async def get_me(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict[str, Any]:
    """Compatibility endpoint — prefer /profile for editable fields."""
    org = await _organization_payload()
    perms = _permissions_payload(user)
    profile: dict[str, Any] = {
        "sub": user.sub,
        "username": user.username,
        "email": user.email,
        "first_name": None,
        "last_name": None,
        "email_verified": False,
        "totp_configured": False,
        "required_actions": [],
        **org,
        **perms,
    }
    client = get_keycloak_admin_client()
    try:
        summary = await client.get_user(user.sub)
        profile.update(
            {
                "email": summary.email or user.email,
                "first_name": summary.first_name,
                "last_name": summary.last_name,
                "email_verified": summary.email_verified,
                "totp_configured": summary.totp_configured,
                "required_actions": summary.required_actions,
            }
        )
    except KeycloakAdminError:
        logger.warning("Keycloak profile enrich failed for sub=%s", user.sub)
    return profile


@router.get("/profile")
async def get_profile(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict[str, Any]:
    client = get_keycloak_admin_client()
    try:
        summary = await client.get_user(user.sub)
    except KeycloakAdminError as exc:
        raise map_keycloak_admin_error(exc) from exc

    org = await _organization_payload()
    perms = _permissions_payload(user)
    return {
        "sub": summary.id,
        "username": summary.username,
        "email": summary.email or "",
        "first_name": summary.first_name or "",
        "last_name": summary.last_name or "",
        "email_verified": summary.email_verified,
        "totp_configured": summary.totp_configured,
        "required_actions": summary.required_actions,
        **org,
        **perms,
    }


@router.patch("/profile")
async def update_profile(
    body: UpdateProfileBody,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict[str, Any]:
    if body.email is None and body.first_name is None and body.last_name is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile fields to update.",
        )
    if body.email is not None and "@" not in body.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email looks invalid.",
        )

    client = get_keycloak_admin_client()
    try:
        summary = await client.update_user(
            user.sub,
            email=body.email.strip() if body.email is not None else None,
            first_name=body.first_name,
            last_name=body.last_name,
        )
    except KeycloakAdminError as exc:
        raise map_keycloak_admin_error(exc) from exc

    logger.info("user updated profile username=%s", user.username)
    org = await _organization_payload()
    perms = _permissions_payload(user)
    return {
        "sub": summary.id,
        "username": summary.username,
        "email": summary.email or "",
        "first_name": summary.first_name or "",
        "last_name": summary.last_name or "",
        "email_verified": summary.email_verified,
        "totp_configured": summary.totp_configured,
        "required_actions": summary.required_actions,
        **org,
        **perms,
    }


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def change_password(
    body: ChangePasswordBody,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> Response:
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password.",
        )

    client = get_keycloak_admin_client()
    try:
        summary = await client.get_user(user.sub)
        valid = await client.verify_user_password(
            summary.username, body.current_password
        )
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )
        await client.reset_user_password(user.sub, body.new_password)
    except KeycloakAdminError as exc:
        raise map_keycloak_admin_error(exc) from exc

    logger.info("user changed password username=%s", user.username)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/security")
async def security_info(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    client = get_keycloak_admin_client()
    try:
        profile = await client.sync_totp_state(user.sub)
    except KeycloakAdminError as exc:
        raise map_keycloak_admin_error(exc) from exc

    pending = "CONFIGURE_TOTP" in profile.required_actions
    return {
        "username": profile.username,
        "email": profile.email or user.email,
        "totp_supported": True,
        "totp_configured": profile.totp_configured,
        "required_actions": profile.required_actions,
        "setup_pending": pending,
        "frontend_url": settings.frontend_url,
        "steps": [
            "Click Enable MFA in Relay — this flags your account for authenticator setup.",
            "Sign out of Relay, then sign in again.",
            "Keycloak will prompt you to scan a QR code with an authenticator app (part of login).",
            "Return here and click Confirm MFA setup so Relay clears any stale setup flag.",
        ],
        "hint": (
            "MFA is enabled from Relay. Credential storage stays in Keycloak (identity provider); "
            "you do not need the Keycloak account console."
        ),
    }


@router.post("/require-2fa")
async def require_own_2fa(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict[str, Any]:
    client = get_keycloak_admin_client()
    try:
        profile = await client.require_totp_setup(user.sub)
    except KeycloakAdminError as exc:
        raise map_keycloak_admin_error(exc) from exc

    return {
        "user_id": profile.id,
        "totp_configured": profile.totp_configured,
        "required_actions": profile.required_actions,
        "setup_pending": "CONFIGURE_TOTP" in profile.required_actions,
        "message": "Sign out and sign back in to complete authenticator setup.",
    }


@router.post("/sync-2fa")
async def sync_account_2fa(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict[str, Any]:
    client = get_keycloak_admin_client()
    try:
        profile = await client.sync_totp_state(user.sub)
    except KeycloakAdminError as exc:
        raise map_keycloak_admin_error(exc) from exc

    return {
        "user_id": profile.id,
        "totp_configured": profile.totp_configured,
        "required_actions": profile.required_actions,
        "setup_pending": "CONFIGURE_TOTP" in profile.required_actions,
        "message": (
            "Authenticator is active."
            if profile.totp_configured
            else "No authenticator credential found yet — finish setup on next login."
        ),
    }
