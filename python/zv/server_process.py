from __future__ import annotations

import os
import subprocess
import threading
import uvicorn
import sys
from typing import Optional

from api.server import app as fastapi_app

class ServerProcess:
    def __init__(self) -> None:
        self.proc: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None
        self._server: Optional[uvicorn.Server] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        config = uvicorn.Config(
            fastapi_app,
            host="127.0.0.1",
            port=8000,
            reload=False,
            access_log=False,
            log_level="warning"
        )
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()

    def is_dead(self) -> bool:
        if self._thread is None:
            return False
        return not self._thread.is_alive()

    def stop(self) -> None:
        if self._server:
            try:
                self._server.should_exit = True
            except Exception:
                pass
        self._server = None
        self._thread = None