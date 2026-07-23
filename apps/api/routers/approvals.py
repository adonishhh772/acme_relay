"""HITL approvals inbox — durable Postgres queue (not in-memory)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth.dependencies import CurrentUser, require_permission
from services.approvals_store import (
    count_pending_approvals,
    decide_approval,
    list_pending_approvals,
    persist_staged_approvals,
)

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


class ApprovalDecision(BaseModel):
    approval_id: str
    approve: bool
    action_text: str | None = None
    issue_key: str | None = None
    owner: str | None = None


class StageApprovalRequest(BaseModel):
    approval: dict[str, Any] = Field(...)


@router.post("/stage")
async def stage_approval(
    body: StageApprovalRequest,
    user: Annotated[CurrentUser, Depends(require_permission("create_next_action"))],
) -> dict[str, Any]:
    approval = dict(body.approval)
    approval.setdefault("requested_by", user.username)
    approval.setdefault("tool", approval.get("tool") or "create_next_action")
    ids = await persist_staged_approvals(
        request_id=str(approval.get("request_id") or f"stage-{user.sub}"),
        session_id=str(approval.get("session_id") or "manual-stage"),
        created_by_sub=user.sub,
        pending=[approval],
    )
    return {"ok": True, "approval_id": ids[0] if ids else approval.get("approval_id")}


@router.get("")
async def list_approvals(
    user: Annotated[CurrentUser, Depends(require_permission("create_next_action"))],
) -> dict[str, Any]:
    _ = user
    items = await list_pending_approvals()
    return {"items": items, "total": len(items)}


@router.get("/count")
async def approvals_count(
    user: Annotated[CurrentUser, Depends(require_permission("create_next_action"))],
) -> dict[str, Any]:
    _ = user
    return {"pending": await count_pending_approvals()}


@router.post("/decide")
async def decide(
    body: ApprovalDecision,
    user: Annotated[CurrentUser, Depends(require_permission("approve_next_action"))],
) -> dict[str, Any]:
    result = await decide_approval(
        approval_id=body.approval_id,
        approve=body.approve,
        decided_by_sub=user.sub,
        decided_by_username=user.username,
        action_text=body.action_text,
        issue_key=body.issue_key,
        owner=body.owner,
    )
    if not result.get("ok"):
        detail = str(result.get("error") or "Approval not found")
        status = 404 if "not found" in detail.lower() else 400
        raise HTTPException(status_code=status, detail=detail)
    return result
