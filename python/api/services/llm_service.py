from __future__ import annotations
import json
import requests

OLLAMA_URL = "http://127.0.0.1:11434"
MODEL = "qwen2.5-coder:3b"

''' 
FOR CHATBOT 
'''
CHAT_SYSTEM_PROMPT = (
    "You are Zero, a friendly AI assistant for blind and visually-impaired programmers.\n"
    "Keep answers short and practical.\n"
    "Return ONLY valid JSON with this exact schema:\n"
    "{\n"
    '  "reply": string\n'
    "}\n"
    "No markdown. No extra text."
)

''' 
FOR CODE ANALYSIS 
'''
ANALYZE_SYSTEM_PROMPT = (
    "You are a code explanation assistant for blind and visually-impaired programmers.\n"
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

def _strip_code_fences(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("```"):
        lines = s.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        s = "\n".join(lines).strip()
    return s

def _extract_json_object(s: str) -> str | None:
    s = (s or "").strip()
    if not s:
        return None

    start = s.find("{")
    if start == -1:
        return None

    depth = 0
    in_str = False
    esc = False

    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue

        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]

    return None

def _to_json(content: str) -> dict:
    content = _strip_code_fences(content).strip()
    if not content:
        return {}

    # strict
    try:
        obj = json.loads(content)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # extract first object
    extracted = _extract_json_object(content)
    if extracted:
        try:
            obj = json.loads(extracted)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass

    return {}

def ollama_chat(user_message: str, *, temperature: float = 0.3, num_predict: int = 120) -> dict:
    payload = {
        "model": MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
        },
    }

    r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
    r.raise_for_status()
    raw = r.json()["message"]["content"]
    data = _to_json(raw)

    reply = data.get("reply")
    if isinstance(reply, str) and reply.strip():
        return {"reply": reply}

    return {"reply": _strip_code_fences(raw).strip() or "No response."}

def ollama_analyze(code: str, language: str, *, temperature: float = 0.2, num_predict: int = 220) -> dict:
    payload = {
        "model": MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": ANALYZE_SYSTEM_PROMPT},
            {"role": "user", "content": f"Language: {language}\n\nCode:\n{code}\n"},
        ],
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
        },
    }

    r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=180)
    r.raise_for_status()
    raw = r.json()["message"]["content"]
    data = _to_json(raw)

    steps = data.get("steps")
    narration = data.get("narration")

    if not isinstance(steps, list) or not all(isinstance(x, str) for x in steps):
        steps = []

    if not isinstance(narration, str):
        narration = ""

    return {"steps": steps, "narration": narration}