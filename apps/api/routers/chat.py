import time
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends

from agent.graph import invoke_agent
from agent.groundedness import apply_groundedness_policy, verify_groundedness
from agent.tools import ToolContext
from auth.dependencies import CurrentUser, get_current_user
from config import Settings, get_settings
from memory.session_store import append_message
from schemas.chat import ChatRequest, ChatResponse, GroundednessPayload
from support.db import acquire
from telemetry.langfuse_tracing import finalize_agent_run_trace

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChatResponse:
    _ = settings
    session_id = body.session_id or uuid4().hex
    request_id = uuid4().hex
    ctx = ToolContext(
        user_sub=user.sub,
        username=user.username,
        roles=user.roles,
        session_id=session_id,
        request_id=request_id,
    )
    await append_message(session_id, "user", body.query)
    started = time.perf_counter()
    result = await invoke_agent(body.query, ctx, thread_id=session_id)
    latency_ms = int((time.perf_counter() - started) * 1000)
    raw_answer = result["answer"] or "I could not produce an answer from tools."
    tool_calls: list[dict[str, Any]] = result.get("tool_calls") or []
    verification = verify_groundedness(raw_answer, tool_calls)
    answer = apply_groundedness_policy(raw_answer, verification)
    groundedness = GroundednessPayload(
        passed=verification.passed,
        unsupported_claims=verification.unsupported_claims,
        evidence_ids_used=verification.evidence_ids_used,
        explanation=verification.explanation,
    )
    await append_message(session_id, "assistant", answer)
    role_values = [role.value for role in user.roles]
    async with acquire() as connection:
        await connection.execute(
            """
            INSERT INTO agent_runs (
                request_id, user_sub, query, answer, tools_used, latency_ms,
                prompt_name, prompt_version, groundedness_passed, groundedness_explanation
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            request_id,
            user.sub,
            body.query,
            answer,
            result["tools_used"],
            latency_ms,
            result["prompt_name"],
            result["prompt_version"],
            groundedness.passed,
            groundedness.explanation,
        )
    finalize_agent_run_trace(
        request_id=request_id,
        query=body.query,
        answer=answer,
        tools_used=result["tools_used"],
        latency_ms=latency_ms,
        prompt_name=result["prompt_name"],
        prompt_version=result["prompt_version"],
        user_sub=user.sub,
        session_id=session_id,
        roles=role_values,
        pending_approvals=len(result["pending_approvals"]),
    )
    return ChatResponse(
        answer=answer,
        session_id=session_id,
        request_id=request_id,
        tools_used=result["tools_used"],
        pending_approvals=result["pending_approvals"],
        prompt_name=result["prompt_name"],
        prompt_version=result["prompt_version"],
        latency_ms=latency_ms,
        groundedness=groundedness,
    )
