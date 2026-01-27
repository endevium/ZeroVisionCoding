from __future__ import annotations

import json
import requests

# =========================
# Configuration
# =========================

OLLAMA_URL = "http://127.0.0.1:11434"
MODEL = "qwen2.5-coder:3b"

SYSTEM_PROMPT = (
    "You are a friendly AI chatbot.\n"
    "Your name is Zero and you are a Zero Vision Coding AI Assistant.\n"
    "Your description is that you are an AI-enhanced Braille programming platform designed to empower blind and visually-impaired programmers by providing them with advanced tools that facilitate coding through an Arduino-based Braille keyboard.\n"
    "You cannot write any code as you are only supposed to assist blind and visually-impaired programmers.\n"
    "You can only assist in frontend and backend development.\n"
    "Reply conversationally and clearly.\n"
    "Return ONLY valid JSON with this exact schema:\n"
    "{\n"
    '  "reply": string\n'
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

def _extract_json_object(s: str) -> str | None:
    """
    Best-effort: find the first top-level JSON object in a messy model response.
    """
    s = s.strip()
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

def _to_reply_json(content: str) -> dict:
    """
    Always return a dict like {'reply': string}, even if the model didn't output JSON.
    """
    content = _strip_code_fences(content).strip()

    if not content:
        return {"reply": "I didn't get a response from the model. Please try again."}

    # 1) Try strict parse
    try:
        data = json.loads(content)
        if isinstance(data, dict) and isinstance(data.get("reply"), str):
            return data
    except json.JSONDecodeError:
        pass

    # 2) Try extracting JSON object from mixed text
    extracted = _extract_json_object(content)
    if extracted:
        try:
            data = json.loads(extracted)
            if isinstance(data, dict) and isinstance(data.get("reply"), str):
                return data
        except json.JSONDecodeError:
            pass

    # 3) Fallback: wrap raw text
    # (Optional) strip leading "Sure," etc. Keep it simple.
    return {"reply": content}

def chat(message: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]

    payload = {
        "model": MODEL,
        "stream": False,
        "messages": messages,
        "options": {"temperature": 0.7},
    }

    response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
    response.raise_for_status()

    raw = response.json()["message"]["content"]
    return _to_reply_json(raw)

def main():
    print("Welcome to Zero Vision Coding")
    while True:
        prompt = input("You: ")

        print("Zero is thinking...")
        bot = chat(prompt)
        print(bot["reply"])

if __name__ == "__main__":
    main()