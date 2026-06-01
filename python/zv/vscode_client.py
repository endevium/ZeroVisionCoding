from __future__ import annotations

from typing import Any, Dict
import requests


class VSCodeClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def ping(self) -> bool:
        try:
            r = requests.get(self.base_url + "/vscode/status", timeout=1.5)
            return r.ok
        except Exception:
            return False

    def vscode_status(self) -> Dict[str, Any]:
        try:
            r = requests.get(self.base_url + "/vscode/status", timeout=2.0)
            if not r.ok:
                return {"connected": False}
            data = r.json()
            return {
                "connected": bool(data.get("connected")),
                "name": data.get("name"),
                "version": data.get("version"),
            }
        except Exception:
            return {"connected": False}

    def editor(self) -> Dict[str, Any]:
        try:
            r = requests.get(self.base_url + "/vscode/editor", timeout=2.0)
            return r.json() if r.ok else {}
        except Exception:
            return {}

    def terminal_snapshot(self) -> Dict[str, Any]:
        try:
            r = requests.get(self.base_url + "/terminal/snapshot", timeout=2.0)
            return r.json() if r.ok else {}
        except Exception:
            return {}
    
    def terminal_reset(self) -> Dict[str, Any]:
        try:
            r = requests.post(self.base_url + "/terminal/reset", json={}, timeout=2.0)
            return r.json() if r.ok else {"ok": False}
        except Exception:
            return {"ok": False}

    def enqueue_command(self, typ: str, payload: dict) -> Dict[str, Any]:
        try:
            r = requests.post(
                self.base_url + "/vscode/command",
                json={"type": typ, "payload": payload},
                timeout=3.0,
            )
            return r.json() if r.ok else {"ok": False}
        except Exception:
            return {"ok": False}

    def command_result(self, cmd_id: str) -> Dict[str, Any]:
        try:
            r = requests.get(self.base_url + f"/vscode/command-result/{cmd_id}", timeout=2.0)
            if r.status_code == 404:
                return {}
            return r.json() if r.ok else {"ok": False, "message": f"HTTP {r.status_code}"}
        except Exception:
            return {}

    def analyze_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        try:
            r = requests.post(
                self.base_url + "/llm/analyze",
                json={"code": code, "language": language},
                timeout=180,
            )
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, dict) else {"steps": [], "narration": ""}
        except Exception:
            return {"steps": [], "narration": "Code analysis failed. The local LLM service returned an error."}
        
    def analyze_active_editor(self) -> Dict[str, Any]:
        try:
            r = requests.post(self.base_url + "/analyze-active-editor", timeout=30.0)
            return r.json() if r.ok else {"ok": False}
        except Exception:
            return {"ok": False}

    def chat(self, message: str) -> Dict[str, Any]:
        try:
            r = requests.post(self.base_url + "/chat", json={"message": message}, timeout=35.0)
            return r.json() if r.ok else {"reply": ""}
        except Exception:
            return {"reply": ""}
    
    def explain_symbol(self, code: str, language: str, symbol: str, kind: str = "") -> Dict[str, Any]:
        try:
            r = requests.post(
                self.base_url + "/llm/explain_symbol",
                json={"code": code, "language": language, "symbol": symbol, "kind": kind},
                timeout=60.0,
            )
            return r.json() if r.ok else {"summary": "", "details": []}
        except Exception:
            return {"summary": "Explain failed.", "details": []}
    
    def fix_python_error(self, code: str, error: str) -> Dict[str, Any]:
        try:
            r = requests.post(
                self.base_url + "/llm/fix-python-error",
                json={"code": code, "error": error},
                timeout=180,
            )
            return r.json() if r.ok else {"content": "", "summary": "Fix request failed."}
        except Exception:
            return {"content": "", "summary": "Fix request failed."}

    def apply_file_content(self, path: str, content: str) -> Dict[str, Any]:
        return self.enqueue_command("apply_file_content", {"path": path, "content": content})