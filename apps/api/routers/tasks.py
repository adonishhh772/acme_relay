from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from auth.dependencies import CurrentUser, require_permission
from support.db import acquire

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    description: str | None = None
    priority: str = "medium"
    due_at: datetime | None = None
    issue_key: str | None = None
    customer_external_id: str | None = None


@router.get("")
async def list_tasks(
    user: Annotated[CurrentUser, Depends(require_permission("manage_tasks"))],
) -> dict[str, Any]:
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT id, title, description, priority, status, due_at,
                   issue_key, customer_external_id, created_at, completed_at
            FROM user_tasks
            WHERE keycloak_sub = $1
            ORDER BY
              CASE status WHEN 'open' THEN 0 ELSE 1 END,
              CASE priority
                WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                WHEN 'medium' THEN 3 ELSE 4
              END,
              created_at DESC
            """,
            user.sub,
        )
    return {"items": [dict(row) for row in rows]}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    user: Annotated[CurrentUser, Depends(require_permission("manage_tasks"))],
) -> dict[str, Any]:
    async with acquire() as connection:
        org_id = await connection.fetchval(
            "SELECT id FROM organizations WHERE slug = 'acme-ops' LIMIT 1"
        )
        row = await connection.fetchrow(
            """
            INSERT INTO user_tasks (
                keycloak_sub, organization_id, title, description, priority,
                due_at, issue_key, customer_external_id
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, title, description, priority, status, due_at,
                      issue_key, customer_external_id, created_at
            """,
            user.sub,
            org_id,
            body.title.strip(),
            body.description,
            body.priority,
            body.due_at,
            body.issue_key,
            body.customer_external_id,
        )
    return dict(row)


@router.post("/{task_id}/complete")
async def complete_task(
    task_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("manage_tasks"))],
) -> dict[str, Any]:
    async with acquire() as connection:
        row = await connection.fetchrow(
            """
            UPDATE user_tasks
            SET status = 'completed', completed_at = now(), updated_at = now()
            WHERE id = $1 AND keycloak_sub = $2
            RETURNING id, status, completed_at
            """,
            task_id,
            user.sub,
        )
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return dict(row)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("manage_tasks"))],
) -> None:
    async with acquire() as connection:
        result = await connection.execute(
            "DELETE FROM user_tasks WHERE id = $1 AND keycloak_sub = $2",
            task_id,
            user.sub,
        )
    if result.endswith("0"):
        raise HTTPException(status_code=404, detail="Task not found")
