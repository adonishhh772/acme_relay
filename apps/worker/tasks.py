from __future__ import annotations

import asyncio
import os
from pathlib import Path

import asyncpg
from celery import Celery

from embeddings import embed_texts, vector_literal

BROKER = os.environ.get("CELERY_BROKER_URL", "redis://:redis_secret@localhost:6381/1")
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://relay:relay_secret@localhost:5434/relay_ops"
)
KNOWLEDGE_ROOT = Path(os.environ.get("KNOWLEDGE_ROOT", "/data/knowledge"))

app = Celery("relay_worker", broker=BROKER)


def _run(coro):
    return asyncio.run(coro)


async def _embed_and_store(document_id: str | None, force: bool) -> dict:
    pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=3)
    try:
        async with pool.acquire() as connection:
            if document_id:
                docs = await connection.fetch(
                    """
                    SELECT id, title, source_path, allowed_roles, sensitivity::text
                    FROM knowledge_documents WHERE id = $1::uuid
                    """,
                    document_id,
                )
            else:
                docs = await connection.fetch(
                    """
                    SELECT id, title, source_path, allowed_roles, sensitivity::text
                    FROM knowledge_documents
                    WHERE ingest_status = 'pending' OR $1::bool
                    """,
                    force,
                )
            ingested = 0
            for doc in docs:
                relative = str(doc["source_path"]).removeprefix("/data/knowledge/")
                path = KNOWLEDGE_ROOT / relative
                if not path.is_file():
                    await connection.execute(
                        """
                        UPDATE knowledge_documents
                        SET ingest_status = 'missing_file', updated_at = now()
                        WHERE id = $1
                        """,
                        doc["id"],
                    )
                    continue
                text = path.read_text(encoding="utf-8")
                chunks = [
                    text[index : index + 800]
                    for index in range(0, len(text), 800)
                    if text[index : index + 800].strip()
                ]
                vectors = await embed_texts(chunks)
                async with connection.transaction():
                    await connection.execute(
                        "DELETE FROM knowledge_chunks WHERE document_id = $1", doc["id"]
                    )
                    for index, (content, vector) in enumerate(zip(chunks, vectors, strict=True)):
                        await connection.execute(
                            """
                            INSERT INTO knowledge_chunks
                              (document_id, chunk_index, content, embedding, allowed_roles, sensitivity)
                            VALUES ($1, $2, $3, $4::vector, $5, $6::knowledge_sensitivity)
                            """,
                            doc["id"],
                            index,
                            content,
                            vector_literal(vector),
                            list(doc["allowed_roles"]),
                            doc["sensitivity"],
                        )
                    await connection.execute(
                        """
                        UPDATE knowledge_documents
                        SET ingest_status = 'ready', updated_at = now()
                        WHERE id = $1
                        """,
                        doc["id"],
                    )
                ingested += 1
            return {"ok": True, "ingested": ingested}
    finally:
        await pool.close()


@app.task(name="tasks.ingest_knowledge")
def ingest_knowledge(
    document_id: str | None = None,
    force: bool = False,
    requested_by: str = "system",
) -> dict:
    result = _run(_embed_and_store(document_id, force))
    result["requested_by"] = requested_by
    return result
