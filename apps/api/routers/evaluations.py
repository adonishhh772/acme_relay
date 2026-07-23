"""Evaluation suite API — list history + run live suite with step progress."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from auth.dependencies import CurrentUser, require_permission
from services.eval_runner import get_run_status, load_questions, start_suite
from support.db import acquire

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])


@router.get("/suite")
async def get_eval_suite(
    user: Annotated[CurrentUser, Depends(require_permission("run_evals"))],
) -> dict[str, Any]:
    _ = user
    questions = load_questions()
    return {
        "suite_name": "relay-live-suite",
        "total": len(questions),
        "questions": [
            {
                "id": item["id"],
                "role": item["role"],
                "query": item["query"],
                "notes": item.get("notes"),
                "expect_permission_denied": bool(item.get("expect_permission_denied")),
            }
            for item in questions
        ],
    }


@router.get("/run/status")
async def eval_run_status(
    user: Annotated[CurrentUser, Depends(require_permission("run_evals"))],
) -> dict[str, Any]:
    _ = user
    return get_run_status()


@router.post("/run")
async def start_eval_run(
    user: Annotated[CurrentUser, Depends(require_permission("run_evals"))],
) -> dict[str, Any]:
    _ = user
    current = get_run_status()
    if current.get("status") == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An evaluation suite is already running.",
        )
    return await start_suite()


@router.get("/runs")
async def list_eval_runs(
    user: Annotated[CurrentUser, Depends(require_permission("run_evals"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT id, suite_name, question_id, role_name, passed, score,
                   latency_ms, details, created_at
            FROM eval_runs
            ORDER BY created_at DESC
            LIMIT 100
            """
        )
        summary = await connection.fetchrow(
            """
            SELECT count(*) AS total,
                   count(*) FILTER (WHERE passed) AS passed,
                   avg(latency_ms)::int AS avg_latency_ms
            FROM eval_runs
            """
        )
    return {
        "summary": dict(summary)
        if summary
        else {"total": 0, "passed": 0, "avg_latency_ms": None},
        "items": [dict(row) for row in rows],
        "run_status": get_run_status(),
    }
