from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

@dataclass
class CommandItem:
    id: str
    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: time.time())

class CommandQueue:
    def __init__(self) -> None:
        self._lock = Lock()
        self._queue: list[CommandItem] = []
        self._results: dict[str, dict[str, Any]] = {}

    def enqueue(self, type: str, payload: dict[str, Any] | None = None) -> CommandItem:
        item = CommandItem(id=str(uuid.uuid4()), type=type, payload=payload or {})
        with self._lock:
            self._queue.append(item)
        return item

    def next(self) -> CommandItem | None:
        with self._lock:
            if not self._queue:
                return None
            return self._queue.pop(0)

    def set_result(self, command_id: str, ok: bool, message: str | None = None, data: dict[str, Any] | None = None) -> None:
        with self._lock:
            self._results[command_id] = {
                "id": command_id,
                "ok": bool(ok),
                "message": message or "",
                "data": data or {},
                "ts": time.time(),
            }

    def get_result(self, command_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._results.get(command_id)

QUEUE = CommandQueue()