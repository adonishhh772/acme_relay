from dataclasses import dataclass, field
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.keycloak import verify_bearer_token
from auth.rbac import has_permission, roles_from_claims
from config import Settings, get_settings
from schemas.enums import Role

security = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    sub: str
    username: str
    email: str
    roles: set[Role] = field(default_factory=set)

    def can(self, permission: str) -> bool:
        return has_permission(self.roles, permission)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    if settings.auth_disabled_for_tests:
        return CurrentUser(
            sub="test-admin",
            username="test-admin",
            email="test@acme.local",
            roles={Role.ADMIN},
        )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token"
        )
    claims = await verify_bearer_token(credentials.credentials, settings)
    realm_access = claims.get("realm_access") or {}
    role_names = list(realm_access.get("roles") or [])
    roles = roles_from_claims(role_names)
    if not roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No recognised Relay roles"
        )
    return CurrentUser(
        sub=str(claims.get("sub")),
        username=str(claims.get("preferred_username") or claims.get("sub")),
        email=str(claims.get("email") or ""),
        roles=roles,
    )


def require_permission(permission: str):
    async def dependency(
        user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if not user.can(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}",
            )
        return user

    return dependency
