from functools import lru_cache
from typing import Any

import httpx
import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient

from config import Settings


@lru_cache
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True)


async def verify_bearer_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        client = _jwks_client(settings.jwks_url)
        signing_key = client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="account",
            issuer=settings.issuer,
            options={"verify_aud": False},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


async def keycloak_ready(settings: Settings) -> bool:
    url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)
            return response.status_code == 200
    except httpx.HTTPError:
        return False
