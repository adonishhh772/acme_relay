"""Live progress events for SSE chat streaming."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RunProgressEmitter:
    request_id: str
    queue: asyncio.Queue[tuple[str, dict[str, Any]]] = field(
        default_factory=asyncio.Queue
    )

    async def emit(self, event_type: str, **payload: Any) -> None:
        event = {
            "type": event_type,
            "at": utc_now_iso(),
            "request_id": self.request_id,
            **payload,
        }
        await self.queue.put(("progress", event))
