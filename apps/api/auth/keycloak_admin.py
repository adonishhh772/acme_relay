"""Keycloak Admin REST client for in-app profile, password, and MFA status."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from fastapi import HTTPException

from config import Settings, get_settings

logger = logging.getLogger("relay.keycloak_admin")

CONFIGURE_TOTP_ACTION = "CONFIGURE_TOTP"
GENERIC_ADMIN_ERROR = "Identity administration is temporarily unavailable."
APP_REALM_ROLES = frozenset(
    {"sales_user", "support_user", "operations_user", "admin"}
)


class KeycloakAdminError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class KeycloakUserSummary:
    id: str
    username: str
    email: str | None
    first_name: str | None
    last_name: str | None
    email_verified: bool
    roles: list[str] = field(default_factory=list)
    totp_configured: bool = False
    required_actions: list[str] = field(default_factory=list)


class KeycloakAdminClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def _admin_base(self) -> str:
        return (
            f"{self._settings.keycloak_url.rstrip('/')}"
            f"/admin/realms/{self._settings.keycloak_realm}"
        )

    async def verify_user_password(self, username: str, password: str) -> bool:
        token_url = (
            f"{self._settings.keycloak_issuer.rstrip('/')}"
            f"/realms/{self._settings.keycloak_realm}/protocol/openid-connect/token"
        )
        data = {
            "grant_type": "password",
            "client_id": self._settings.keycloak_frontend_client_id,
            "username": username,
            "password": password,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(token_url, data=data)
        except httpx.HTTPError as exc:
            logger.exception("Keycloak password verification failed")
            raise KeycloakAdminError(GENERIC_ADMIN_ERROR) from exc
        return response.status_code == 200

    async def reset_user_password(
        self,
        user_id: str,
        password: str,
        *,
        temporary: bool = False,
    ) -> None:
        await self._admin_request(
            "PUT",
            f"/users/{user_id}/reset-password",
            json_body={
                "type": "password",
                "value": password,
                "temporary": temporary,
            },
            expected_status=(204,),
        )

    async def _request_admin_token(self) -> tuple[str, float]:
        token_url = (
            f"{self._settings.keycloak_url.rstrip('/')}"
            "/realms/master/protocol/openid-connect/token"
        )
        data = {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": self._settings.keycloak_admin_user,
            "password": self._settings.keycloak_admin_password,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(token_url, data=data)
        except httpx.HTTPError as exc:
            logger.exception("Keycloak admin token request failed")
            raise KeycloakAdminError(GENERIC_ADMIN_ERROR) from exc

        if response.status_code != 200:
            logger.error(
                "Keycloak admin token rejected status=%s body=%s",
                response.status_code,
                response.text[:200],
            )
            raise KeycloakAdminError(GENERIC_ADMIN_ERROR, status_code=503)

        payload = response.json()
        access_token = payload.get("access_token")
        expires_in = float(payload.get("expires_in", 60))
        if not access_token:
            raise KeycloakAdminError(GENERIC_ADMIN_ERROR, status_code=503)
        return access_token, time.monotonic() + expires_in

    async def _get_admin_token(self) -> str:
        async with self._lock:
            if self._token and time.monotonic() < self._token_expires_at - 30:
                return self._token
            token, expires_at = await self._request_admin_token()
            self._token = token
            self._token_expires_at = expires_at
            return token

    async def _admin_request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | list[Any] | None = None,
        params: dict[str, str | int] | None = None,
        expected_status: tuple[int, ...] = (200, 201, 204),
    ) -> httpx.Response:
        token = await self._get_admin_token()
        url = f"{self._admin_base}{path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    json=json_body,
                    params=params,
                )
        except httpx.HTTPError as exc:
            logger.exception(
                "Keycloak admin request failed method=%s path=%s", method, path
            )
            raise KeycloakAdminError(GENERIC_ADMIN_ERROR) from exc

        if response.status_code not in expected_status:
            logger.warning(
                "Keycloak admin unexpected status=%s method=%s path=%s body=%s",
                response.status_code,
                method,
                path,
                response.text[:300],
            )
            if response.status_code == 404:
                raise KeycloakAdminError("User not found.", status_code=404)
            if response.status_code == 409:
                raise KeycloakAdminError("Conflict with existing identity data.", status_code=409)
            raise KeycloakAdminError(GENERIC_ADMIN_ERROR, status_code=502)
        return response

    async def _get_user_roles(self, user_id: str) -> list[str]:
        response = await self._admin_request(
            "GET",
            f"/users/{user_id}/role-mappings/realm",
        )
        roles = response.json()
        names = [role["name"] for role in roles if isinstance(role, dict)]
        return [name for name in names if name in APP_REALM_ROLES]

    async def _user_has_totp(self, user_id: str) -> bool:
        response = await self._admin_request("GET", f"/users/{user_id}/credentials")
        credentials = response.json()
        return any(
            isinstance(item, dict) and item.get("type") == "otp" for item in credentials
        )

    async def _sync_stale_totp_required_action(
        self,
        user_id: str,
        raw: dict[str, Any],
        totp_configured: bool,
    ) -> dict[str, Any]:
        actions = list(raw.get("requiredActions") or [])
        if not totp_configured or CONFIGURE_TOTP_ACTION not in actions:
            return raw

        logger.info(
            "clearing stale CONFIGURE_TOTP user_id=%s username=%s",
            user_id,
            raw.get("username"),
        )
        updated = dict(raw)
        updated["requiredActions"] = [
            action for action in actions if action != CONFIGURE_TOTP_ACTION
        ]
        await self._admin_request(
            "PUT",
            f"/users/{user_id}",
            json_body=updated,
            expected_status=(204,),
        )
        return updated

    def _map_user_summary(
        self,
        raw: dict[str, Any],
        roles: list[str],
        totp: bool,
    ) -> KeycloakUserSummary:
        return KeycloakUserSummary(
            id=str(raw.get("id", "")),
            username=str(raw.get("username", "")),
            email=raw.get("email"),
            first_name=raw.get("firstName"),
            last_name=raw.get("lastName"),
            email_verified=bool(raw.get("emailVerified", False)),
            roles=roles,
            totp_configured=totp,
            required_actions=list(raw.get("requiredActions") or []),
        )

    async def get_user(self, user_id: str) -> KeycloakUserSummary:
        response = await self._admin_request("GET", f"/users/{user_id}")
        raw = response.json()
        totp = await self._user_has_totp(user_id)
        raw = await self._sync_stale_totp_required_action(user_id, raw, totp)
        roles = await self._get_user_roles(user_id)
        return self._map_user_summary(raw, roles, totp)

    async def sync_totp_state(self, user_id: str) -> KeycloakUserSummary:
        return await self.get_user(user_id)

    async def update_user(
        self,
        user_id: str,
        *,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> KeycloakUserSummary:
        response = await self._admin_request("GET", f"/users/{user_id}")
        body = response.json()
        if email is not None:
            body["email"] = email
        if first_name is not None:
            body["firstName"] = first_name
        if last_name is not None:
            body["lastName"] = last_name

        await self._admin_request(
            "PUT",
            f"/users/{user_id}",
            json_body=body,
            expected_status=(204,),
        )
        return await self.get_user(user_id)

    async def require_totp_setup(self, user_id: str) -> KeycloakUserSummary:
        response = await self._admin_request("GET", f"/users/{user_id}")
        body = response.json()
        actions = list(body.get("requiredActions") or [])
        if CONFIGURE_TOTP_ACTION not in actions:
            actions.append(CONFIGURE_TOTP_ACTION)
        body["requiredActions"] = actions
        await self._admin_request(
            "PUT",
            f"/users/{user_id}",
            json_body=body,
            expected_status=(204,),
        )
        return await self.get_user(user_id)

    async def clear_totp_requirement(self, user_id: str) -> KeycloakUserSummary:
        """Remove CONFIGURE_TOTP required action without deleting OTP credentials."""
        response = await self._admin_request("GET", f"/users/{user_id}")
        body = response.json()
        actions = [
            action
            for action in list(body.get("requiredActions") or [])
            if action != CONFIGURE_TOTP_ACTION
        ]
        body["requiredActions"] = actions
        await self._admin_request(
            "PUT",
            f"/users/{user_id}",
            json_body=body,
            expected_status=(204,),
        )
        return await self.get_user(user_id)

    async def disable_totp(self, user_id: str) -> KeycloakUserSummary:
        """Remove OTP credentials and clear CONFIGURE_TOTP so MFA is off."""
        response = await self._admin_request("GET", f"/users/{user_id}/credentials")
        credentials = response.json()
        for item in credentials:
            if not isinstance(item, dict) or item.get("type") != "otp":
                continue
            credential_id = item.get("id")
            if not credential_id:
                continue
            await self._admin_request(
                "DELETE",
                f"/users/{user_id}/credentials/{credential_id}",
                expected_status=(204,),
            )
        return await self.clear_totp_requirement(user_id)


_keycloak_admin_client: KeycloakAdminClient | None = None


def get_keycloak_admin_client() -> KeycloakAdminClient:
    global _keycloak_admin_client
    if _keycloak_admin_client is None:
        _keycloak_admin_client = KeycloakAdminClient()
    return _keycloak_admin_client


def map_keycloak_admin_error(exc: KeycloakAdminError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))
