"""Durable HITL approvals — pending_approvals table + seeded next_actions."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from support.db import acquire


def _approval_from_pending_row(row: Any) -> dict[str, Any]:
    arguments = row["arguments"]
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    arguments = dict(arguments or {})
    return {
        "approval_id": str(row["id"]),
        "source": "pending_approvals",
        "tool": row["tool_name"],
        "issue_key": arguments.get("issue_key"),
        "action_text": arguments.get("action_text"),
        "owner": arguments.get("owner"),
        "status": arguments.get("status") or row["status"],
        "comment": arguments.get("comment"),
        "requested_by": arguments.get("requested_by") or row["created_by_sub"],
        "request_id": row["request_id"],
        "session_id": row["session_id"],
        "created_at": row["created_at"].isoformat()
        if hasattr(row["created_at"], "isoformat")
        else row["created_at"],
    }


def _approval_from_next_action_row(row: Any) -> dict[str, Any]:
    return {
        "approval_id": str(row["id"]),
        "source": "next_actions",
        "tool": "create_next_action",
        "issue_key": row["issue_key"],
        "action_text": row["action_text"],
        "owner": row["owner"],
        "status": "pending",
        "requested_by": row.get("created_by_sub") or row["owner"],
        "created_at": row["created_at"].isoformat()
        if hasattr(row["created_at"], "isoformat")
        else row["created_at"],
    }


async def persist_staged_approvals(
    *,
    request_id: str,
    session_id: str,
    created_by_sub: str,
    pending: list[dict[str, Any]],
) -> list[str]:
    """Write chat-staged HITL items into pending_approvals. Returns inserted ids."""
    if not pending:
        return []
    inserted: list[str] = []
    async with acquire() as connection:
        for item in pending:
            approval_id = str(item.get("approval_id") or uuid4().hex)
            tool_name = str(item.get("tool") or "unknown")
            arguments = {
                "approval_id": approval_id,
                "issue_key": item.get("issue_key"),
                "action_text": item.get("action_text"),
                "owner": item.get("owner"),
                "status": item.get("status") or item.get("status_label") or "pending_approval",
                "comment": item.get("comment"),
                "requested_by": item.get("requested_by"),
            }
            row_id = await connection.fetchval(
                """
                INSERT INTO pending_approvals (
                    request_id, session_id, tool_name, arguments, created_by_sub, status
                )
                VALUES ($1, $2, $3, $4::jsonb, $5, 'pending')
                RETURNING id::text
                """,
                request_id,
                session_id,
                tool_name,
                json.dumps(arguments),
                created_by_sub,
            )
            inserted.append(str(row_id))
            item["approval_id"] = str(row_id)
            item["source"] = "pending_approvals"
    return inserted


async def list_pending_approvals() -> list[dict[str, Any]]:
    async with acquire() as connection:
        staged = await connection.fetch(
            """
            SELECT id::text, request_id, session_id, tool_name, arguments,
                   created_by_sub, status::text AS status, created_at
            FROM pending_approvals
            WHERE status = 'pending'
            ORDER BY created_at DESC
            """
        )
        seeded = await connection.fetch(
            """
            SELECT na.id::text, na.action_text, na.owner, na.created_by_sub, na.created_at,
                   i.issue_key
            FROM next_actions na
            JOIN issues i ON i.id = na.issue_id
            WHERE na.status = 'pending'
            ORDER BY na.created_at DESC
            """
        )
    items = [_approval_from_pending_row(row) for row in staged]
    items.extend(_approval_from_next_action_row(row) for row in seeded)
    return items


async def count_pending_approvals() -> int:
    async with acquire() as connection:
        staged = await connection.fetchval(
            "SELECT count(*) FROM pending_approvals WHERE status = 'pending'"
        )
        seeded = await connection.fetchval(
            "SELECT count(*) FROM next_actions WHERE status = 'pending'"
        )
    return int(staged or 0) + int(seeded or 0)


async def decide_approval(
    *,
    approval_id: str,
    approve: bool,
    decided_by_sub: str,
    decided_by_username: str,
    action_text: str | None = None,
    issue_key: str | None = None,
    owner: str | None = None,
) -> dict[str, Any]:
    async with acquire() as connection:
        async with connection.transaction():
            staged = await connection.fetchrow(
                """
                SELECT id::text, tool_name, arguments, created_by_sub, status::text AS status
                FROM pending_approvals
                WHERE id::text = $1
                FOR UPDATE
                """,
                approval_id,
            )
            if staged is not None:
                if staged["status"] != "pending":
                    return {
                        "ok": False,
                        "error": f"Approval already {staged['status']}",
                    }
                arguments = staged["arguments"]
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                arguments = dict(arguments or {})
                new_status = "approved" if approve else "rejected"
                await connection.execute(
                    """
                    UPDATE pending_approvals
                    SET status = $2::next_action_status,
                        decided_by_sub = $3,
                        decided_at = now(),
                        updated_at = now()
                    WHERE id::text = $1
                    """,
                    approval_id,
                    new_status,
                    decided_by_sub,
                )
                if not approve:
                    return {
                        "ok": True,
                        "status": "rejected",
                        "approval_id": approval_id,
                    }
                if staged["tool_name"] == "create_next_action":
                    resolved_issue = str(
                        arguments.get("issue_key") or issue_key or ""
                    ).upper()
                    resolved_action = str(
                        arguments.get("action_text") or action_text or ""
                    )
                    resolved_owner = str(
                        arguments.get("owner") or owner or decided_by_username
                    )
                    issue_id = await connection.fetchval(
                        "SELECT id FROM issues WHERE issue_key = $1",
                        resolved_issue,
                    )
                    if issue_id is None:
                        return {"ok": False, "error": "Issue not found"}
                    row = await connection.fetchrow(
                        """
                        INSERT INTO next_actions (
                            issue_id, action_text, owner, status, created_by_sub, approved_by_sub
                        )
                        VALUES ($1, $2, $3, 'approved', $4, $5)
                        RETURNING id::text, status::text, action_text, owner
                        """,
                        issue_id,
                        resolved_action,
                        resolved_owner,
                        staged["created_by_sub"] or arguments.get("requested_by"),
                        decided_by_sub,
                    )
                    return {
                        "ok": True,
                        "status": "approved",
                        "approval_id": approval_id,
                        "next_action": dict(row),
                    }
                return {
                    "ok": True,
                    "status": "approved",
                    "approval_id": approval_id,
                    "tool": staged["tool_name"],
                    "note": "Issue update approved — apply manually in desk if needed.",
                }

            next_action = await connection.fetchrow(
                """
                SELECT na.id::text, na.action_text, na.owner, na.status::text AS status,
                       i.issue_key
                FROM next_actions na
                JOIN issues i ON i.id = na.issue_id
                WHERE na.id::text = $1
                FOR UPDATE
                """,
                approval_id,
            )
            if next_action is None:
                return {"ok": False, "error": "Approval not found"}
            if next_action["status"] != "pending":
                return {
                    "ok": False,
                    "error": f"Next action already {next_action['status']}",
                }
            new_status = "approved" if approve else "rejected"
            row = await connection.fetchrow(
                """
                UPDATE next_actions
                SET status = $2::next_action_status,
                    approved_by_sub = CASE WHEN $2::text = 'approved' THEN $3 ELSE approved_by_sub END,
                    updated_at = now()
                WHERE id::text = $1
                RETURNING id::text, status::text, action_text, owner
                """,
                approval_id,
                new_status,
                decided_by_sub,
            )
            return {
                "ok": True,
                "status": new_status,
                "approval_id": approval_id,
                "issue_key": next_action["issue_key"],
                "next_action": dict(row) if row else None,
            }
