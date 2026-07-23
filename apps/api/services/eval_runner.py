"""In-app eval suite runner with step-by-step progress for the Evaluations UI."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from auth.dependencies import CurrentUser
from schemas.chat import ChatRequest
from schemas.enums import Role
from services.eval_scoring import score_question
from support.db import acquire

logger = logging.getLogger("relay.eval")

SUITE_NAME = "relay-live-suite"

ROLE_USERS: dict[str, CurrentUser] = {
    "sales_user": CurrentUser(
        sub="eval-sales",
        username="alice",
        email="alice@acme.local",
        roles={Role.SALES},
    ),
    "support_user": CurrentUser(
        sub="eval-support",
        username="bob",
        email="bob@acme.local",
        roles={Role.SUPPORT},
    ),
    "operations_user": CurrentUser(
        sub="eval-ops",
        username="dana",
        email="dana@acme.local",
        roles={Role.OPERATIONS},
    ),
    "admin": CurrentUser(
        sub="eval-admin",
        username="admin",
        email="admin@acme.local",
        roles={Role.ADMIN},
    ),
}

_lock = asyncio.Lock()
_state: dict[str, Any] = {
    "status": "idle",
    "suite_name": SUITE_NAME,
    "started_at": None,
    "completed_at": None,
    "error": None,
    "progress": 0,
    "total": 0,
    "current_step": None,
    "steps": [],
    "summary": None,
}


def questions_file() -> Path:
    candidates: list[Path] = [
        Path("/app/evals/eval_questions.json"),
        Path(__file__).resolve().parents[1] / "evals" / "eval_questions.json",
    ]
    # Host checkout: apps/api/services → repo root is parents[3]
    resolved = Path(__file__).resolve()
    if len(resolved.parents) > 3:
        candidates.append(resolved.parents[3] / "evals" / "eval_questions.json")
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("eval_questions.json not found (mount ./evals or run from repo)")


def load_questions() -> list[dict[str, Any]]:
    return json.loads(questions_file().read_text(encoding="utf-8"))


def get_run_status() -> dict[str, Any]:
    return dict(_state)


def _init_steps(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for index, item in enumerate(questions, start=1):
        steps.append(
            {
                "step": index,
                "label": f"Step {index} of {len(questions)}",
                "question_id": item["id"],
                "role": item["role"],
                "query": item["query"],
                "status": "pending",
                "passed": None,
                "latency_ms": None,
                "tools_used": [],
                "error": None,
                "answer_preview": None,
            }
        )
    return steps


async def _persist_result(row: dict[str, Any]) -> None:
    score = 1.0 if row["passed"] else 0.0
    details = {
        "tools_used": row["tools_used"],
        "tool_pass": row["tool_pass"],
        "grounded": row["grounded"],
        "rbac_pass": row["rbac_pass"],
        "next_action_pass": row["next_action_pass"],
        "error": row.get("error"),
        "answer_preview": row.get("answer_preview"),
        "query": row.get("query"),
    }
    async with acquire() as connection:
        await connection.execute(
            """
            INSERT INTO eval_runs (
                suite_name, question_id, role_name, passed, score, latency_ms, details
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
            """,
            SUITE_NAME,
            row["id"],
            row["role"],
            row["passed"],
            score,
            row["latency_ms"],
            json.dumps(details),
        )


async def _run_suite() -> None:
    from routers.chat import run_chat_turn

    questions = load_questions()
    _state["status"] = "running"
    _state["started_at"] = datetime.now(UTC).isoformat()
    _state["completed_at"] = None
    _state["error"] = None
    _state["progress"] = 0
    _state["total"] = len(questions)
    _state["steps"] = _init_steps(questions)
    _state["summary"] = None
    _state["current_step"] = (
        f"Step 1 of {len(questions)} · {questions[0]['id']}" if questions else None
    )

    results: list[dict[str, Any]] = []
    try:
        for index, item in enumerate(questions):
            step = _state["steps"][index]
            step["status"] = "running"
            _state["current_step"] = (
                f"Step {index + 1} of {len(questions)} · {item['id']} ({item['role']})"
            )
            _state["progress"] = index

            user = ROLE_USERS.get(item["role"])
            if user is None:
                scored = score_question(item, None, f"Unknown role {item['role']}")
            else:
                try:
                    response = await run_chat_turn(
                        ChatRequest(
                            query=item["query"],
                            session_id=f"eval-ui-{item['id']}-{uuid4().hex[:8]}",
                        ),
                        user,
                    )
                    payload = response.model_dump()
                    scored = score_question(item, payload, None)
                except Exception as exc:  # noqa: BLE001 — surface per-step failures
                    logger.exception("eval step failed id=%s", item["id"])
                    scored = score_question(item, None, str(exc))

            results.append(scored)
            step["status"] = "passed" if scored["passed"] else "failed"
            step["passed"] = scored["passed"]
            step["latency_ms"] = scored["latency_ms"]
            step["tools_used"] = scored["tools_used"]
            step["error"] = scored.get("error")
            step["answer_preview"] = scored.get("answer_preview")
            _state["progress"] = index + 1
            await _persist_result(scored)

        total = len(results)
        passed = sum(1 for row in results if row["passed"])
        avg_latency = (
            int(sum(row["latency_ms"] for row in results) / total) if total else None
        )
        _state["summary"] = {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round((passed / total) * 100, 1) if total else 0.0,
            "tool_selection_pass": sum(1 for row in results if row["tool_pass"]),
            "groundedness_pass": sum(1 for row in results if row["grounded"]),
            "rbac_pass": sum(1 for row in results if row["rbac_pass"]),
            "next_action_pass": sum(1 for row in results if row["next_action_pass"]),
            "avg_latency_ms": avg_latency,
        }
        _state["status"] = "completed"
        _state["current_step"] = f"Completed · {passed}/{total} passed"
    except Exception as exc:  # noqa: BLE001
        logger.exception("eval suite failed")
        _state["status"] = "failed"
        _state["error"] = str(exc)
        _state["current_step"] = f"Failed · {exc}"
    finally:
        _state["completed_at"] = datetime.now(UTC).isoformat()


async def start_suite() -> dict[str, Any]:
    async with _lock:
        if _state["status"] == "running":
            return get_run_status()
        questions = load_questions()
        _state["status"] = "running"
        _state["progress"] = 0
        _state["total"] = len(questions)
        _state["steps"] = _init_steps(questions)
        _state["error"] = None
        _state["summary"] = None
        _state["started_at"] = datetime.now(UTC).isoformat()
        _state["completed_at"] = None
        _state["current_step"] = (
            f"Step 1 of {len(questions)} · starting…" if questions else "No questions"
        )
        asyncio.create_task(_run_suite())
        return get_run_status()
