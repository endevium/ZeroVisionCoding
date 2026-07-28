from __future__ import annotations

import json
import requests
import subprocess
import base64

# =========================
# Configuration
# =========================

import os
import sys

# Ensure python directory is in sys.path to import from api
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "python"))
from api.services.llm_service import llm_analyze

# =========================
# Helpers
# =========================

def _strip_code_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        lines = s.splitlines()
        lines = lines[1:] 
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        s = "\n".join(lines).strip()
    return s

def speak_text_windows(text: str, rate: int = 0, volume: int = 100, voice: str | None = None) -> None:
    text_b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")

    ps_script = f"""
$bytes = [System.Convert]::FromBase64String("{text_b64}")
$text  = [System.Text.Encoding]::UTF8.GetString($bytes)

$voice = New-Object -ComObject SAPI.SpVoice
$voice.Rate = {int(rate)}
$voice.Volume = {int(volume)}

{"$voiceName = " + repr(voice) + "; $voice.GetVoices() | ForEach-Object { if ($_.GetDescription() -like ('*' + $voiceName + '*')) { $voice.Voice = $_ } }" if voice else ""}

$voice.Speak($text) | Out-Null
""".strip()

    encoded = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
        check=True,
    )

def summarize_code(code: str, language: str) -> dict:
    data = llm_analyze(code, language)
    
    steps = data.get("steps")
    narration = data.get("narration")

    if not isinstance(steps, list) or not all(isinstance(x, str) for x in steps) or not steps:
        raise RuntimeError(f"Expected 'steps' to be non-empty list[str]. Raw: {data}")

    if not isinstance(narration, str) or not narration.strip():
        raise RuntimeError(f"Expected 'narration' to be non-empty string. Raw: {data}")

    return data

def main():
    code = """\
"""
    print("Please wait while we analyze your code...")
    speak_text_windows("Please wait while we analyze your code", rate=0, volume=100, voice=None)
    summary = summarize_code(code, "javascript")
    
    narration = summary["narration"]
    print(narration)

    speak_text_windows(narration, rate=0, volume=100, voice="David")

if __name__ == "__main__":
    main()