from __future__ import annotations

import json
import requests
import speech_recognition as sr
import pyttsx3
import re
import base64
import subprocess

# =========================
# Configuration
# =========================sass

OLLAMA_URL = "http://127.0.0.1:11434"
MODEL = "qwen2.5-coder:3b"
WAKE_WORDS = ("hello",)
SPEAK_REPLIES = False

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

def chat(message: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]

    payload = {
        "model": MODEL,
        "stream": False,
        "messages": messages,
        "options": {
            "temperature": 0.3,
            "num_predict": 120,
        },
    }

    response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
    response.raise_for_status()

    raw = response.json()["message"]["content"]
    return _to_reply_json(raw)

def _speak(text: str, engine: pyttsx3.Engine | None) -> None:
    if not engine:
        return
    engine.say(text)
    engine.runAndWait()

_WORD_RE = re.compile(r"[a-z0-9']+", re.IGNORECASE)

def _normalize_words(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text)]

def _extract_after_wake(text: str) -> str | None:
    words = _normalize_words(text)
    if not words:
        return None

    for ww in WAKE_WORDS:
        ww_words = _normalize_words(ww)
        if not ww_words:
            continue

        # Find the wake phrase as a contiguous sequence
        for i in range(0, len(words) - len(ww_words) + 1):
            if words[i : i + len(ww_words)] == ww_words:
                remainder_words = words[i + len(ww_words) :]
                return "" if not remainder_words else " ".join(remainder_words)

    return None

def speech_loop(device_index: int | None = None) -> None:
    r = sr.Recognizer()
    engine = pyttsx3.init() if SPEAK_REPLIES else None

    list_mics()

    try:
        mic = sr.Microphone(device_index=device_index)
    except Exception as e:
        print(f"Failed to open microphone (device_index={device_index}): {e}")
        return

    with mic as source:
        r.adjust_for_ambient_noise(source, duration=0.8)
        print(f"Speech mode on. Wake words: {WAKE_WORDS}. Ctrl+C to stop.")

        while True:
            print("Listening...")
            speak_text_windows("Listening...", rate=0, volume=100, voice="David")
            try:
                audio = r.listen(source, timeout=None, phrase_time_limit=6)
            except Exception as e:
                print(f"Listen error: {e}")
                continue

            try:
                heard = r.recognize_google(audio)
                print(f"Heard: {heard}")
            except sr.UnknownValueError:
                print("Heard audio but could not understand.")
                speak_text_windows("Audio could not be understood", rate=0, volume=100, voice="David")
                continue
            except sr.RequestError as e:
                print(f"Speech recognition request error (internet?): {e}")
                continue

            remainder = _extract_after_wake(heard)
            if remainder is None:
                print("Command not heard")
                speak_text_windows("Command not heard...", rate=0, volume=100, voice="David")
                continue

            prompt = "How can I help?" if remainder == "" else remainder

            print("Zero is thinking...")
            speak_text_windows("Zero is thinking...", rate=0, volume=100, voice="David")
            bot = chat(prompt)
            reply = bot.get("reply", "")
            print(reply)
            speak_text_windows(reply, rate=0, volume=100, voice="David")
            _speak(reply, engine)

def list_mics() -> None:
    print("Microphone devices:")
    names = sr.Microphone.list_microphone_names()
    if not names:
        print("  (none found)")
        return
    for i, name in enumerate(names):
        print(f"  [{i}] {name}")

def main():
    print(list_mics())
    print("Welcome to Zero Vision Coding")
    mode = input("Type 't' for text chat or 's' for speech: ").strip().lower()

    if mode == "s":
        idx = input("Mic device index (blank for default): ").strip()
        device_index = int(idx) if idx else None
        speech_loop(device_index=device_index)
        return

    while True:
        prompt = input("You: ")
        print("Zero is thinking...")
        bot = chat(prompt)
        print(bot["reply"])

if __name__ == "__main__":
    main()