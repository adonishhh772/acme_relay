from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth.dependencies import CurrentUser, require_permission
from support.db import acquire

router = APIRouter(prefix="/api/approvals", tags=["approvals"])

# In-memory pending approvals for demo (also mirrored when tools stage them via chat response).
_PENDING: dict[str, dict[str, Any]] = {}


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
    approval_id = str(approval.get("approval_id"))
    approval["staged_by"] = user.username
    _PENDING[approval_id] = approval
    return {"ok": True, "approval_id": approval_id}


@router.get("")
async def list_approvals(
    user: Annotated[CurrentUser, Depends(require_permission("create_next_action"))],
) -> dict[str, Any]:
    _ = user
    return {"items": list(_PENDING.values())}


@router.post("/decide")
async def decide(
    body: ApprovalDecision,
    user: Annotated[CurrentUser, Depends(require_permission("approve_next_action"))],
) -> dict[str, Any]:
    pending = _PENDING.pop(body.approval_id, None)
    if pending is None and body.issue_key and body.action_text:
        pending = {
            "issue_key": body.issue_key,
            "action_text": body.action_text,
            "owner": body.owner or user.username,
        }
    if pending is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    if not body.approve:
        return {"ok": True, "status": "rejected", "approval_id": body.approval_id}
    issue_key = str(pending.get("issue_key") or body.issue_key or "")
    action_text = str(pending.get("action_text") or body.action_text or "")
    owner = str(pending.get("owner") or body.owner or user.username)
    async with acquire() as connection:
        async with connection.transaction():
            issue_id = await connection.fetchval(
                "SELECT id FROM issues WHERE issue_key = $1",
                issue_key.upper(),
            )
            if issue_id is None:
                raise HTTPException(status_code=404, detail="Issue not found")
            row = await connection.fetchrow(
                """
                INSERT INTO next_actions (issue_id, action_text, owner, status, created_by_sub, approved_by_sub)
                VALUES ($1, $2, $3, 'approved', $4, $5)
                RETURNING id::text, status::text, action_text, owner
                """,
                issue_id,
                action_text,
                owner,
                pending.get("requested_by"),
                user.sub,
            )
    return {"ok": True, "status": "approved", "next_action": dict(row)}
