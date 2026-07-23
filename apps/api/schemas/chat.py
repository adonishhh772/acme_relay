from typing import Any

from pydantic import BaseModel, Field


class GroundednessPayload(BaseModel):
    passed: bool
    unsupported_claims: list[str] = Field(default_factory=list)
    evidence_ids_used: list[str] = Field(default_factory=list)
    explanation: str


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=8000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    request_id: str
    tools_used: list[str]
    pending_approvals: list[dict[str, Any]]
    prompt_name: str
    prompt_version: int
    latency_ms: int
    grounded: bool | None = None
    groundedness: GroundednessPayload | None = None


class McpServerStatus(BaseModel):
    name: str
    url: str
    reachable: bool
    status_code: int | None = None
    error: str | None = None


class McpStatusResponse(BaseModel):
    mcp_server_url: str
    reachable: bool
    status_code: int | None = None
    error: str | None = None
    servers: list[McpServerStatus] = Field(default_factory=list)
    agent_tools_enabled: bool = False
    agent_tools_loaded: bool = False
    agent_tool_count: int = 0
    agent_tools_error: str | None = None
