from typing import Any

from config import get_settings

_checkpointer = None


async def get_redis_checkpointer():
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer
    settings = get_settings()
    try:
        from langgraph.checkpoint.redis.aio import AsyncRedisSaver

        _checkpointer = AsyncRedisSaver(redis_url=settings.redis_url)
        await _checkpointer.asetup()
        return _checkpointer
    except Exception:
        from langgraph.checkpoint.memory import MemorySaver

        _checkpointer = MemorySaver()
        return _checkpointer


def graph_config(
    *,
    thread_id: str,
    callbacks: list[Any] | None = None,
    metadata: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    run_name: str = "relay-agent",
) -> dict[str, Any]:
    config: dict[str, Any] = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 12,
        "run_name": run_name,
    }
    if callbacks:
        config["callbacks"] = callbacks
    if metadata:
        config["metadata"] = metadata
    if tags:
        config["tags"] = tags
    return config
