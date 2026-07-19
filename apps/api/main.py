import logging
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from agent.mcp_client import is_mcp_enabled, mcp_load_status, warm_mcp_tools
from auth.dependencies import CurrentUser, get_current_user
from auth.keycloak import keycloak_ready
from config import get_settings
from routers import (
    account,
    admin,
    approvals,
    audit,
    chat,
    desk,
    evaluations,
    governance,
    knowledge,
    tasks,
)
from schemas.chat import McpServerStatus, McpStatusResponse
from support.db import close_pool, init_pool
from telemetry.setup import configure_observability

logger = logging.getLogger("relay.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    configure_observability(settings)
    await init_pool()
    try:
        await warm_mcp_tools()
    except Exception as exc:
        logger.warning("MCP warm-up failed (non-fatal): %s", exc)
    yield
    await close_pool()


app = FastAPI(title="Relay API", version="0.2.0", lifespan=lifespan)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(desk.router)
app.include_router(approvals.router)
app.include_router(knowledge.router)
app.include_router(audit.router)
app.include_router(governance.router)
app.include_router(tasks.router)
app.include_router(account.router)
app.include_router(admin.router)
app.include_router(evaluations.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "relay-api"}


@app.get("/health/ready")
async def ready() -> dict:
    settings = get_settings()
    kc = await keycloak_ready(settings)
    return {"status": "ready" if kc else "degraded", "keycloak": kc}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/mcp/status", response_model=McpStatusResponse)
async def mcp_status(
    _user: Annotated[CurrentUser, Depends(get_current_user)],
) -> McpStatusResponse:
    """Verify MCP server reachability and agent tool load state."""
    settings = get_settings()

    async def probe(name: str, base_url: str) -> McpServerStatus:
        url = f"{base_url.rstrip('/')}/sse"
        try:
            timeout = httpx.Timeout(5.0, connect=3.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("GET", url) as response:
                    return McpServerStatus(
                        name=name,
                        url=base_url,
                        reachable=response.status_code < 500,
                        status_code=response.status_code,
                    )
        except Exception as exc:
            logger.debug("MCP probe failed name=%s: %s", name, exc)
            return McpServerStatus(
                name=name,
                url=base_url,
                reachable=False,
                error=str(exc) or type(exc).__name__,
            )

    servers = [
        await probe("domain", settings.mcp_domain_url),
        await probe("filesystem", settings.mcp_filesystem_url),
        await probe("postgres", settings.mcp_postgres_url),
    ]
    mcp_tools = mcp_load_status()
    primary = servers[0]
    return McpStatusResponse(
        mcp_server_url=settings.mcp_domain_url,
        reachable=primary.reachable,
        status_code=primary.status_code,
        error=primary.error,
        servers=servers,
        agent_tools_enabled=is_mcp_enabled(),
        agent_tools_loaded=bool(mcp_tools.get("loaded")),
        agent_tool_count=int(mcp_tools.get("tool_count") or 0),
        agent_tools_error=mcp_tools.get("error"),
    )
