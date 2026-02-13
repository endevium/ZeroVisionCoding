from __future__ import annotations

import time
from collections import deque
from threading import Lock
from typing import Any

class EditorRingBuffer:
    def __init__(self, max_items: int = 60) -> None:
        self._lock = Lock()
        self._items: deque[dict[str, Any]] = deque(maxlen=max_items)

    def push(self, snapshot: dict[str, Any]) -> None:
        with self._lock:
            self._items.append({"ts": time.time(), **snapshot})

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._items)

    def tail(self, n: int = 10) -> list[dict[str, Any]]:
        with self._lock:
            if n <= 0:
                return []
            items = list(self._items)
            return items[-n:]

BUFFER = EditorRingBuffer(max_items=60)