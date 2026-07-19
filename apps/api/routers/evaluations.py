from typing import Annotated, Any

from fastapi import APIRouter, Depends

from auth.dependencies import CurrentUser, require_permission
from support.db import acquire

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])


@router.get("/runs")
async def list_eval_runs(
    user: Annotated[CurrentUser, Depends(require_permission("run_evals"))],
) -> dict[str, Any]:
    _ = user
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT id, suite_name, question_id, role_name, passed, score,
                   latency_ms, created_at
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
    }
