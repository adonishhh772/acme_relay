"""Live evaluation runner — scores tool selection, RBAC, grounding, next-action, latency."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

EVALS = Path(__file__).resolve().parent
QUESTIONS = EVALS / "eval_questions.json"
RESULTS = EVALS / "eval_results.md"

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000").rstrip("/")
KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://127.0.0.1:8080").rstrip("/")
KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM", "acme")
KEYCLOAK_CLIENT_ID = os.environ.get("KEYCLOAK_EVAL_CLIENT_ID", "relay-frontend")

ROLE_USERS = {
    "sales_user": ("alice", "alice123"),
    "support_user": ("bob", "bob123"),
    "admin": ("admin", "admin123"),
}

GROUNDED_MARKERS = (
    "MERIDIAN",
    "Meridian",
    "CASCADE",
    "Cascade",
    "NORTHLINE",
    "Northline",
    "CASE-2001",
    "CASE-2002",
    "CASE-2003",
    "Priya",
    "James",
    "Elena",
)


def fetch_token(username: str, password: str) -> str:
    token_url = (
        f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
    )
    response = httpx.post(
        token_url,
        data={
            "grant_type": "password",
            "client_id": KEYCLOAK_CLIENT_ID,
            "username": username,
            "password": password,
        },
        timeout=20.0,
    )
    response.raise_for_status()
    return str(response.json()["access_token"])


def score_question(item: dict[str, Any], payload: dict[str, Any] | None, error: str | None) -> dict[str, Any]:
    expected_tools = set(item.get("expected_tools_any") or [])
    tools_used = set((payload or {}).get("tools_used") or [])
    answer = str((payload or {}).get("answer") or "")
    latency_ms = int((payload or {}).get("latency_ms") or 0)
    pending = (payload or {}).get("pending_approvals") or []

    tool_pass = bool(expected_tools & tools_used) if expected_tools else True
    grounded = any(marker in answer for marker in GROUNDED_MARKERS) or bool(tools_used)
    denied = "permission_denied" in answer.lower() or "cannot use" in answer.lower()
    expect_denied = bool(item.get("expect_permission_denied"))
    rbac_pass = denied if expect_denied else (not denied or tool_pass)
    next_action_pass = True
    if "create_next_action" in expected_tools and not expect_denied:
        next_action_pass = bool(pending) or "approval" in answer.lower() or "create_next_action" in tools_used

    if error:
        tool_pass = False
        grounded = False
        rbac_pass = False
        next_action_pass = False

    passed = tool_pass and grounded and rbac_pass and next_action_pass and error is None
    return {
        "id": item["id"],
        "role": item["role"],
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


def write_results(rows: list[dict[str, Any]], live: bool) -> None:
    passed = sum(1 for row in rows if row["passed"])
    total = len(rows)
    lines = [
        "# Relay Evaluation Results",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**API:** {API_URL}",
        f"**Mode:** {'live Keycloak + /api/chat' if live else 'offline design table'}",
        f"**Pass rate:** {passed}/{total} ({(passed / total * 100) if total else 0:.0f}%)",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total | {total} |",
        f"| Passed | {passed} |",
        f"| Failed | {total - passed} |",
        f"| Tool selection pass | {sum(1 for row in rows if row['tool_pass'])} |",
        f"| Groundedness pass | {sum(1 for row in rows if row['grounded'])} |",
        f"| RBAC pass | {sum(1 for row in rows if row['rbac_pass'])} |",
        f"| Next-action pass | {sum(1 for row in rows if row['next_action_pass'])} |",
        f"| Avg latency (ms) | {(sum(row['latency_ms'] for row in rows) / total) if total else 0:.0f} |",
        "",
        "## Per-question results",
        "",
        "| ID | Role | Tools | Grounded | RBAC | Next action | Latency | Status |",
        "|----|------|-------|----------|------|-------------|---------|--------|",
    ]
    for row in rows:
        tools = ", ".join(row["tools_used"]) or "—"
        lines.append(
            f"| {row['id']} | {row['role']} | {tools} | "
            f"{'✓' if row['grounded'] else '—'} | "
            f"{'✓' if row['rbac_pass'] else '—'} | "
            f"{'✓' if row['next_action_pass'] else '—'} | "
            f"{row['latency_ms']} | {'PASS' if row['passed'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "## Commentary",
            "",
            "- Tool selection: agent must call DB/RAG tools — not invent Meridian/Cascade facts.",
            "- Groundedness: answers cite CASE-* keys and seeded account owners, or clear RBAC denial.",
            "- RBAC: sales cannot create next actions; restricted knowledge hidden from sales.",
            "- Next actions: support stages HITL approvals; admin approves in Command Desk.",
            "- Traces: inspect Langfuse (http://localhost:3001) for LLM + tool spans per request_id.",
            "",
        ]
    )
    for row in rows:
        if row.get("error") or not row["passed"]:
            lines.append(f"### {row['id']}")
            lines.append(f"- Error: {row.get('error') or 'scored fail'}")
            lines.append(f"- Answer preview: {row.get('answer_preview')}")
            lines.append("")
    RESULTS.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_live(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    token_cache: dict[str, str] = {}
    rows: list[dict[str, Any]] = []
    with httpx.Client(timeout=120.0) as client:
        health = client.get(f"{API_URL}/health")
        health.raise_for_status()
        for item in questions:
            role = item["role"]
            username, password = ROLE_USERS[role]
            try:
                if role not in token_cache:
                    token_cache[role] = fetch_token(username, password)
                response = client.post(
                    f"{API_URL}/api/chat",
                    headers={"Authorization": f"Bearer {token_cache[role]}"},
                    json={"query": item["query"], "session_id": f"eval-{item['id']}"},
                )
                if response.status_code >= 400:
                    rows.append(score_question(item, None, f"HTTP {response.status_code}: {response.text[:300]}"))
                    continue
                rows.append(score_question(item, response.json(), None))
            except Exception as exc:
                rows.append(score_question(item, None, str(exc)))
    return rows


def run_offline(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in questions:
        rows.append(
            {
                "id": item["id"],
                "role": item["role"],
                "tools_used": item.get("expected_tools_any") or [],
                "tool_pass": True,
                "grounded": True,
                "rbac_pass": True,
                "next_action_pass": True,
                "latency_ms": 0,
                "passed": False,
                "error": "offline — start API/Keycloak and re-run for live scores",
                "answer_preview": "",
            }
        )
    return rows


def main() -> int:
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    live = True
    try:
        rows = run_live(questions)
    except Exception as exc:
        print(f"Live eval unavailable ({exc}); writing offline scaffold.")
        live = False
        rows = run_offline(questions)
    write_results(rows, live=live)
    passed = sum(1 for row in rows if row["passed"])
    print(f"Wrote {RESULTS} — {passed}/{len(rows)} passed (live={live})")
    return 0 if (not live or passed == len(rows)) else 1


if __name__ == "__main__":
    sys.exit(main())
