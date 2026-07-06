from __future__ import annotations

import os
import subprocess
import sys
from typing import Optional

class ServerProcess:
    def __init__(self) -> None:
        self.proc: Optional[subprocess.Popen] = None

    def start(self) -> None:
        if self.proc and self.proc.poll() is None:
            return

        python_dir = os.path.dirname(os.path.abspath(__file__))
        # repo python/ folder is one up from zv/
        python_root = os.path.abspath(os.path.join(python_dir, ".."))

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "api.server:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--log-level",
            "warning",
            "--no-access-log",
        ]

        self.proc = subprocess.Popen(cmd, cwd=python_root)

    def is_dead(self) -> bool:
        return bool(self.proc) and (self.proc.poll() is not None)

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.proc = None