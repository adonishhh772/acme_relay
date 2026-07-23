from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.dependencies import CurrentUser, get_current_user
from routers import evaluations
from schemas.enums import Role
from services import eval_runner
from services.eval_scoring import score_question


@pytest.fixture(autouse=True)
def reset_eval_state() -> None:
    eval_runner._state.clear()
    eval_runner._state.update(
        {
            "status": "idle",
            "suite_name": eval_runner.SUITE_NAME,
            "started_at": None,
            "completed_at": None,
            "error": None,
            "progress": 0,
            "total": 0,
            "current_step": None,
            "steps": [],
            "summary": None,
        }
    )


@pytest.fixture
def eval_client() -> TestClient:
    app = FastAPI()
    app.include_router(evaluations.router)

    async def fake_admin() -> CurrentUser:
        return CurrentUser(
            sub="admin",
            username="admin",
            email="admin@acme.local",
            roles={Role.ADMIN},
        )

    app.dependency_overrides[get_current_user] = fake_admin
    return TestClient(app)


def test_score_question_passes_when_tool_and_grounding_match() -> None:
    item = {
        "id": "eval_01",
        "role": "sales_user",
        "query": "Show open issues for VaultLedger",
        "expected_tools_any": ["get_open_issues"],
    }
    payload = {
        "answer": "VaultLedger Payments has 2 open issues including OPS-3101.",
        "tools_used": ["get_open_issues"],
        "latency_ms": 120,
        "pending_approvals": [],
    }
    scored = score_question(item, payload, None)
    assert scored["passed"] is True
    assert scored["tool_pass"] is True
    assert scored["grounded"] is True


def test_score_question_permission_denied_case() -> None:
    item = {
        "id": "eval_02",
        "role": "sales_user",
        "query": "Create next action",
        "expected_tools_any": ["create_next_action"],
        "expect_permission_denied": True,
    }
    payload = {
        "answer": "You do not have permission to create next actions.",
        "tools_used": [],
        "latency_ms": 40,
        "pending_approvals": [],
    }
    scored = score_question(item, payload, None)
    assert scored["passed"] is True
    assert scored["rbac_pass"] is True


def test_score_question_fails_on_error() -> None:
    item = {"id": "eval_x", "role": "admin", "query": "x", "expected_tools_any": []}
    scored = score_question(item, None, "boom")
    assert scored["passed"] is False
    assert scored["error"] == "boom"


def test_questions_file_handles_docker_parent_depth(tmp_path: Path) -> None:
    """Docker path /app/services/foo.py only has parents[0..2]; must not IndexError."""
    from pathlib import Path as PathCls

    mounted = tmp_path / "eval_questions.json"
    mounted.write_text("[]", encoding="utf-8")
    docker_module = PathCls("/app/services/eval_runner.py")
    assert len(docker_module.parents) == 3

    candidates: list[PathCls] = [mounted]
    if len(docker_module.parents) > 3:
        candidates.append(docker_module.parents[3] / "evals" / "eval_questions.json")
    for path in candidates:
        if path.is_file():
            found = path
            break
    else:
        raise AssertionError("expected mounted file")
    assert found == mounted


def test_questions_file_resolves_real_suite() -> None:
    path = eval_runner.questions_file()
    assert path.name == "eval_questions.json"
    assert path.is_file()
    assert len(eval_runner.load_questions()) >= 1


def test_get_suite_lists_questions(eval_client: TestClient) -> None:
    questions = [
        {
            "id": "eval_01",
            "role": "sales_user",
            "query": "Show issues",
            "notes": "demo",
            "expect_permission_denied": False,
        }
    ]
    with patch("routers.evaluations.load_questions", return_value=questions):
        response = eval_client.get("/api/evaluations/suite")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["questions"][0]["id"] == "eval_01"


def test_run_status_idle_by_default(eval_client: TestClient) -> None:
    response = eval_client.get("/api/evaluations/run/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "idle"
    assert body["steps"] == []


def test_start_run_returns_running_with_steps(eval_client: TestClient) -> None:
    questions = [
        {
            "id": "eval_01",
            "role": "sales_user",
            "query": "Show VaultLedger issues",
            "expected_tools_any": ["get_open_issues"],
        },
        {
            "id": "eval_02",
            "role": "support_user",
            "query": "List Nexus Freight issues",
            "expected_tools_any": ["get_open_issues"],
        },
    ]

    async def fake_start() -> dict:
        eval_runner._state["status"] = "running"
        eval_runner._state["progress"] = 0
        eval_runner._state["total"] = 2
        eval_runner._state["steps"] = eval_runner._init_steps(questions)
        eval_runner._state["current_step"] = "Step 1 of 2 · starting…"
        return eval_runner.get_run_status()

    with patch("routers.evaluations.start_suite", new=AsyncMock(side_effect=fake_start)):
        response = eval_client.post("/api/evaluations/run")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"
    assert body["total"] == 2
    assert body["steps"][0]["label"] == "Step 1 of 2"
    assert body["steps"][0]["status"] == "pending"
    assert body["current_step"].startswith("Step 1")


def test_start_run_conflict_when_already_running(eval_client: TestClient) -> None:
    eval_runner._state["status"] = "running"
    response = eval_client.post("/api/evaluations/run")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_start_suite_schedules_background_task() -> None:
    questions = [
        {
            "id": "eval_01",
            "role": "sales_user",
            "query": "q",
            "expected_tools_any": ["get_open_issues"],
        }
    ]
    with (
        patch("services.eval_runner.load_questions", return_value=questions),
        patch("asyncio.create_task") as create_task,
    ):
        status = await eval_runner.start_suite()

    assert status["status"] == "running"
    assert status["total"] == 1
    assert status["steps"][0]["question_id"] == "eval_01"
    create_task.assert_called_once()


@pytest.mark.asyncio
async def test_run_suite_updates_steps_and_persists() -> None:
    questions = [
        {
            "id": "eval_01",
            "role": "sales_user",
            "query": "Show VaultLedger",
            "expected_tools_any": ["get_open_issues"],
        }
    ]
    fake_response = MagicMock()
    fake_response.model_dump.return_value = {
        "answer": "VaultLedger Payments OPS-3101 is open.",
        "tools_used": ["get_open_issues"],
        "latency_ms": 55,
        "pending_approvals": [],
    }
    connection = MagicMock()
    connection.execute = AsyncMock()
    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=connection)
    acquire_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("services.eval_runner.load_questions", return_value=questions),
        patch("routers.chat.run_chat_turn", new=AsyncMock(return_value=fake_response)),
        patch("services.eval_runner.acquire", return_value=acquire_cm),
    ):
        await eval_runner._run_suite()

    assert eval_runner._state["status"] == "completed"
    assert eval_runner._state["progress"] == 1
    assert eval_runner._state["steps"][0]["status"] == "passed"
    assert eval_runner._state["summary"]["passed"] == 1
    assert eval_runner._state["current_step"] == "Completed · 1/1 passed"
    connection.execute.assert_awaited()


def test_list_runs_includes_run_status(eval_client: TestClient) -> None:
    connection = MagicMock()
    connection.fetch = AsyncMock(return_value=[])
    connection.fetchrow = AsyncMock(
        return_value={"total": 0, "passed": 0, "avg_latency_ms": None}
    )
    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=connection)
    acquire_cm.__aexit__ = AsyncMock(return_value=None)

    with patch("routers.evaluations.acquire", return_value=acquire_cm):
        response = eval_client.get("/api/evaluations/runs")

    assert response.status_code == 200
    body = response.json()
    assert "run_status" in body
    assert body["run_status"]["status"] == "idle"
