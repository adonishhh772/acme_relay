from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth.dependencies import CurrentUser, require_permission
from config import get_settings

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class IngestRequest(BaseModel):
    document_id: str | None = None
    force: bool = False


@router.get("/documents")
async def list_documents(
    user: Annotated[CurrentUser, Depends(require_permission("search_knowledge"))],
) -> dict[str, Any]:
    from support.db import acquire

    _ = user
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT id::text, title, source_path, doc_type, sensitivity::text,
                   allowed_roles::text[], ingest_status
            FROM knowledge_documents
            ORDER BY title
            """
        )
    return {"items": [dict(row) for row in rows]}


@router.post("/ingest")
async def enqueue_ingest(
    body: IngestRequest,
    user: Annotated[CurrentUser, Depends(require_permission("ingest_knowledge"))],
) -> dict[str, Any]:
    settings = get_settings()
    from worker_client import enqueue_ingest_task

    task_id = enqueue_ingest_task(
        document_id=body.document_id,
        force=body.force,
        requested_by=user.username,
        broker_url=settings.celery_broker_url,
    )
    return {"ok": True, "task_id": task_id}
