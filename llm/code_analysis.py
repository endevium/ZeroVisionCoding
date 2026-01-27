from __future__ import annotations

import json
import requests

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
        lines = lines[1:]  # drop ``` or ```json
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        s = "\n".join(lines).strip()
    return s

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
    summary = summarize_code(code, "javascript")

    print(summary["narration"])

if __name__ == "__main__":
    main()