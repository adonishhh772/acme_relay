import json
from typing import Any

import redis.asyncio as redis

from config import get_settings

_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(get_settings().redis_url, decode_responses=True)
    return _client


async def append_message(session_id: str, role: str, content: str) -> None:
    client = await get_redis()
    key = f"relay:session:{session_id}:messages"
    await client.rpush(key, json.dumps({"role": role, "content": content}))
    await client.expire(key, 60 * 60 * 12)


async def get_messages(session_id: str, limit: int = 20) -> list[dict[str, Any]]:
    client = await get_redis()
    key = f"relay:session:{session_id}:messages"
    raw_items = await client.lrange(key, -limit, -1)
    return [json.loads(item) for item in raw_items]
