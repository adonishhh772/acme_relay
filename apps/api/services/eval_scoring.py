"""Shared scoring for Relay eval suite (CLI + in-app runner)."""

from __future__ import annotations

import re
from typing import Any

GROUNDED_MARKERS = (
    "VAULTLEDGER",
    "VaultLedger",
    "NEXUSFREIGHT",
    "Nexus Freight",
    "AURORABANK",
    "Aurora Bank",
    "OPS-3101",
    "OPS-3102",
    "OPS-3103",
    "Priya",
    "James",
    "Elena",
)

DENIAL_MARKERS = (
    "permission_denied",
    "cannot use",
    "not allowed",
    "don't have permission",
    "do not have permission",
    "read-only",
    "read only",
    "sales role",
    "insufficient permission",
)


def score_question(
    item: dict[str, Any],
    payload: dict[str, Any] | None,
    error: str | None,
) -> dict[str, Any]:
    expected_tools = set(item.get("expected_tools_any") or [])
    tools_used = set((payload or {}).get("tools_used") or [])
    answer = str((payload or {}).get("answer") or "")
    latency_ms = int((payload or {}).get("latency_ms") or 0)
    pending = (payload or {}).get("pending_approvals") or []
    answer_lower = answer.lower()

    tool_pass = bool(expected_tools & tools_used) if expected_tools else True
    grounded = any(marker in answer for marker in GROUNDED_MARKERS) or bool(tools_used)
    denied = any(marker in answer_lower for marker in DENIAL_MARKERS)
    expect_denied = bool(item.get("expect_permission_denied"))
    if expect_denied:
        mutating_called = bool(expected_tools & tools_used)
        rbac_pass = denied or not mutating_called
        tool_pass = True
        grounded = True
    else:
        rbac_pass = not denied or tool_pass

    next_action_pass = True
    if "create_next_action" in expected_tools and not expect_denied:
        next_action_pass = (
            bool(pending)
            or "approval" in answer_lower
            or "create_next_action" in tools_used
        )

    if error:
        tool_pass = False
        grounded = False
        rbac_pass = False
        next_action_pass = False

    passed = tool_pass and grounded and rbac_pass and next_action_pass and error is None
    return {
        "id": item["id"],
        "role": item["role"],
        "query": item.get("query", ""),
        "notes": item.get("notes", ""),
        "tools_used": sorted(tools_used),
        "tool_pass": tool_pass,
        "grounded": grounded,
        "rbac_pass": rbac_pass,
        "next_action_pass": next_action_pass,
        "latency_ms": latency_ms,
        "passed": passed,
        "error": error,
        "answer_preview": re.sub(r"\s+", " ", answer)[:180],
    }
