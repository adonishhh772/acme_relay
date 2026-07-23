import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from agent.graph import invoke_agent
from agent.groundedness import apply_groundedness_policy, verify_groundedness
from agent.run_progress import RunProgressEmitter
from agent.tools import ToolContext
from auth.dependencies import CurrentUser, get_current_user
from config import Settings, get_settings
from memory.session_store import append_message
from schemas.chat import ChatRequest, ChatResponse, GroundednessPayload
from services.approvals_store import persist_staged_approvals
from support.db import acquire
from telemetry.langfuse_tracing import finalize_agent_run_trace

logger = logging.getLogger("relay.chat")

router = APIRouter(prefix="/api/chat", tags=["chat"])


async def _persist_and_trace(
    *,
    user: CurrentUser,
    session_id: str,
    request_id: str,
    query: str,
    answer: str,
    tools_used: list[str],
    latency_ms: int,
    prompt_name: str,
    prompt_version: int,
    groundedness: GroundednessPayload,
    pending_approvals: list[dict[str, Any]],
) -> None:
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
            query,
            answer,
            tools_used,
            latency_ms,
            prompt_name,
            prompt_version,
            groundedness.passed,
            groundedness.explanation,
        )
    await persist_staged_approvals(
        request_id=request_id,
        session_id=session_id,
        created_by_sub=user.sub,
        pending=pending_approvals,
    )
    finalize_agent_run_trace(
        request_id=request_id,
        query=query,
        answer=answer,
        tools_used=tools_used,
        latency_ms=latency_ms,
        prompt_name=prompt_name,
        prompt_version=prompt_version,
        user_sub=user.sub,
        session_id=session_id,
        roles=role_values,
        pending_approvals=len(pending_approvals),
    )


async def run_chat_turn(
    body: ChatRequest,
    user: CurrentUser,
    *,
    progress: RunProgressEmitter | None = None,
    request_id: str | None = None,
) -> ChatResponse:
    session_id = body.session_id or uuid4().hex
    resolved_request_id = request_id or uuid4().hex
    ctx = ToolContext(
        user_sub=user.sub,
        username=user.username,
        roles=user.roles,
        session_id=session_id,
        request_id=resolved_request_id,
        progress=progress,
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
    await _persist_and_trace(
        user=user,
        session_id=session_id,
        request_id=resolved_request_id,
        query=body.query,
        answer=answer,
        tools_used=result["tools_used"],
        latency_ms=latency_ms,
        prompt_name=result["prompt_name"],
        prompt_version=result["prompt_version"],
        groundedness=groundedness,
        pending_approvals=result["pending_approvals"],
    )
    return ChatResponse(
        answer=answer,
        session_id=session_id,
        request_id=resolved_request_id,
        tools_used=result["tools_used"],
        pending_approvals=result["pending_approvals"],
        prompt_name=result["prompt_name"],
        prompt_version=result["prompt_version"],
        latency_ms=latency_ms,
        grounded=groundedness.passed,
        groundedness=groundedness,
    )


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChatResponse:
    _ = settings
    return await run_chat_turn(body, user)


async def stream_chat_events(
    body: ChatRequest,
    user: CurrentUser,
) -> AsyncIterator[str]:
    request_id = uuid4().hex
    queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()
    progress = RunProgressEmitter(request_id, queue=queue)

    async def runner_task() -> None:
        try:
            response = await run_chat_turn(
                body,
                user,
                progress=progress,
                request_id=request_id,
            )
            await queue.put(("done", response.model_dump(mode="json")))
        except Exception as exc:
            logger.exception("chat stream failed request_id=%s", request_id)
            await queue.put(
                ("error", {"message": str(exc), "status_code": 500})
            )

    task = asyncio.create_task(runner_task())
    yield f"event: started\ndata: {json.dumps({'request_id': request_id})}\n\n"
    try:
        while True:
            kind, payload = await queue.get()
            if kind == "progress":
                yield f"event: progress\ndata: {json.dumps(payload, default=str)}\n\n"
            elif kind == "done":
                yield f"event: done\ndata: {json.dumps(payload, default=str)}\n\n"
                break
            elif kind == "error":
                yield f"event: error\ndata: {json.dumps(payload, default=str)}\n\n"
                break
    finally:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> StreamingResponse:
    return StreamingResponse(
        stream_chat_events(body, user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
