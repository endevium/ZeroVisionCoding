from __future__ import annotations

import json
import requests
import subprocess
import base64

# =========================
# Configuration
# =========================

OLLAMA_URL = "http://127.0.0.1:11434"
MODEL = "qwen2.5-coder:3b"

SYSTEM_PROMPT = (
    "You are a code explanation assistant.\n"
    "Explain the code in short, simple steps.\n"
    "Then produce a single narration paragraph that links the steps using transitions like:\n"
    "\"This first... Next... Then... After that... Finally...\".\n"
    "Use simple language, avoid jargon unless explained.\n"
    "Return ONLY valid JSON with this exact schema:\n"
    "{\n"
    '  "steps": [string, ...],\n'
    '  "narration": string\n'
    "}\n"
    "No markdown. No extra text."
)

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
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Language: {language}\n\n"
                f"Code:\n{code}\n\n"
                "Provide the JSON now."
            ),
        },
    ]

    payload = {
        "model": MODEL,
        "stream": False,
        "messages": messages,
        "options": {"temperature": 0.2},
    }

    response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
    response.raise_for_status()

    content = _strip_code_fences(response.json()["message"]["content"])

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON returned: {e}\nRaw:\n{content}")

    if not isinstance(data, dict):
        raise RuntimeError(f"Expected JSON object. Raw:\n{content}")

    steps = data.get("steps")
    narration = data.get("narration")

    if not isinstance(steps, list) or not all(isinstance(x, str) for x in steps):
        raise RuntimeError(f"Expected 'steps' to be list[str]. Raw:\n{content}")

    if not isinstance(narration, str) or not narration.strip():
        raise RuntimeError(f"Expected 'narration' to be non-empty string. Raw:\n{content}")

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