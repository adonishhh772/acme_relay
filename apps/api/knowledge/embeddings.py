import hashlib
import math
import struct
from typing import Sequence

from config import get_settings


def _hash_embedding(text: str, dimensions: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    seed = digest
    while len(values) < dimensions:
        for index in range(0, len(seed), 4):
            chunk = seed[index : index + 4]
            if len(chunk) < 4:
                break
            number = struct.unpack(">I", chunk)[0]
            values.append((number / 2**32) * 2.0 - 1.0)
            if len(values) >= dimensions:
                break
        seed = hashlib.sha256(seed).digest()
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]


async def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    settings = get_settings()
    if not settings.openai_api_key:
        return [_hash_embedding(text, settings.embedding_dimension) for text in texts]

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.embeddings.create(
        model=settings.embedding_model, input=list(texts)
    )
    return [item.embedding for item in response.data]


async def embed_query(text: str) -> list[float]:
    vectors = await embed_texts([text])
    return vectors[0]


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"
