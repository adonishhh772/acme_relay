from typing import Any

from auth.rbac import roles_for_knowledge_filter
from knowledge.embeddings import embed_query, vector_literal
from schemas.enums import Role
from support.db import acquire


async def search_knowledge_rbac(
    query: str,
    roles: set[Role],
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    if not roles:
        return []
    role_values = roles_for_knowledge_filter(roles)
    query_vector = await embed_query(query)
    literal = vector_literal(query_vector)
    async with acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT
                c.id::text AS chunk_id,
                c.content,
                c.chunk_index,
                c.sensitivity::text AS sensitivity,
                d.title,
                d.source_path,
                d.doc_type,
                1 - (c.embedding <=> $1::vector) AS score
            FROM knowledge_chunks c
            JOIN knowledge_documents d ON d.id = c.document_id
            WHERE c.allowed_roles && $2::app_role[]
              AND c.embedding IS NOT NULL
            ORDER BY c.embedding <=> $1::vector
            LIMIT $3
            """,
            literal,
            role_values,
            limit,
        )
    return [dict(row) for row in rows]
