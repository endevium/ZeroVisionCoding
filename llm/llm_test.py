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
# =========================

OLLAMA_URL = "http://127.0.0.1:11434"
MODEL = "qwen2.5-coder:3b"
WAKE_WORDS = ("hello", "hey zero", "zero")  # FIX: added more wake words
SPEAK_REPLIES = True                          # FIX: unified speech flag, now controls ALL speech

SAPI_VOICE = "Guy"   # FIX: changed from hardcoded "David" — set your preferred voice here
                      # Options: "Ava", "Jenny", "Guy" (after NaturalVoiceSAPIAdapter install)

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

# FIX: conversation memory — Zero now remembers the conversation
conversation_history: list[dict] = []

# =========================
# Mood-based speech profiles
# FIX: different tones for different situations
# =========================

SPEECH_MOODS = {
    "normal":   {"rate": 0,  "volume": 100},
    "error":    {"rate": -2, "volume": 100},   # slower, more serious
    "success":  {"rate": 2,  "volume": 100},   # upbeat, faster
    "thinking": {"rate": -1, "volume": 80},    # calm, slightly slower
    "reading":  {"rate": 1,  "volume": 100},   # slightly faster for code readout
}


# =========================
# JSON Helpers
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
    return {"reply": content}


# =========================
# TTS (Text-to-Speech)
# =========================

def speak_text_windows(
    text: str,
    rate: int = 0,
    volume: int = 100,
    voice: str | None = None,
) -> None:
    """Speak text using Windows SAPI via PowerShell."""
    # FIX: guard — do nothing if speech is disabled
    if not SPEAK_REPLIES:
        return

    text_b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")

    voice_line = ""
    if voice:
        voice_line = (
            f'$voiceName = {json.dumps(voice)}; '
            '$voice.GetVoices() | ForEach-Object { '
            'if ($_.GetDescription() -like ("*" + $voiceName + "*")) { $voice.Voice = $_ } }'
        )

    ps_script = f"""
$bytes = [System.Convert]::FromBase64String("{text_b64}")
$text  = [System.Text.Encoding]::UTF8.GetString($bytes)

$voice = New-Object -ComObject SAPI.SpVoice
$voice.Rate = {int(rate)}
$voice.Volume = {int(volume)}

{voice_line}

$voice.Speak($text) | Out-Null
""".strip()

    encoded = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
        check=True,
    )


def speak(text: str, mood: str = "normal") -> None:
    """
    FIX: Unified speak function with mood support.
    Use this everywhere instead of calling speak_text_windows() directly.
    mood options: 'normal', 'error', 'success', 'thinking', 'reading'
    """
    if not SPEAK_REPLIES:
        print(f"[TTS disabled] {text}")
        return

    cfg = SPEECH_MOODS.get(mood, SPEECH_MOODS["normal"])
    speak_text_windows(text, rate=cfg["rate"], volume=cfg["volume"], voice=SAPI_VOICE)


# =========================
# LLM Chat
# =========================

def chat(message: str) -> dict:
    """
    FIX: now maintains conversation history so Zero remembers context.
    """
    global conversation_history

    # Add user message to history
    conversation_history.append({"role": "user", "content": message})

    # Build full message list with system prompt + history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

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
    result = _to_reply_json(raw)

    # Save assistant reply to history
    conversation_history.append({"role": "assistant", "content": result.get("reply", "")})

    return result


def reset_conversation() -> None:
    """FIX: lets user reset Zero's memory mid-session."""
    global conversation_history
    conversation_history = []
    speak("Conversation reset. How can I help you?")


# =========================
# Speech Utilities
# =========================

def _speak_pyttsx3(text: str, engine: pyttsx3.Engine | None) -> None:
    """Legacy pyttsx3 fallback — only used if engine is provided."""
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

        for i in range(0, len(words) - len(ww_words) + 1):
            if words[i : i + len(ww_words)] == ww_words:
                remainder_words = words[i + len(ww_words):]
                return "" if not remainder_words else " ".join(remainder_words)

    return None


# =========================
# Microphone
# =========================

def list_mics() -> None:
    # FIX: removed erroneous `print(list_mics())` — function prints itself, returns nothing
    print("Microphone devices:")
    names = sr.Microphone.list_microphone_names()
    if not names:
        print("  (none found)")
        return
    for i, name in enumerate(names):
        print(f"  [{i}] {name}")


# =========================
# Speech Loop
# =========================

def speech_loop(device_index: int | None = None) -> None:
    r = sr.Recognizer()

    # FIX: pyttsx3 engine only initialized if needed as fallback
    engine = pyttsx3.init() if not SPEAK_REPLIES else None

    list_mics()  # FIX: just call, don't print return value

    try:
        mic = sr.Microphone(device_index=device_index)
    except Exception as e:
        print(f"Failed to open microphone (device_index={device_index}): {e}")
        return

    with mic as source:
        r.adjust_for_ambient_noise(source, duration=0.8)
        print(f"Speech mode on. Wake words: {WAKE_WORDS}. Say 'reset' to clear memory. Ctrl+C to stop.")

        while True:
            print("Listening...")
            speak("Listening.", mood="normal")

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
                speak("Sorry, I could not understand that.", mood="error")
                continue
            except sr.RequestError as e:
                print(f"Speech recognition request error (internet?): {e}")
                continue

            # FIX: allow voice reset command
            if _normalize_words(heard) == ["reset"]:
                reset_conversation()
                continue

            remainder = _extract_after_wake(heard)
            if remainder is None:
                print("No wake word detected.")
                speak("I did not hear a wake word.", mood="normal")
                continue

            prompt = "How can I help?" if remainder == "" else remainder

            print("Zero is thinking...")
            speak("Zero is thinking.", mood="thinking")

            try:
                bot = chat(prompt)
                reply = bot.get("reply", "")
                print(reply)
                speak(reply, mood="normal")
                _speak_pyttsx3(reply, engine)
            except Exception as e:
                print(f"Chat error: {e}")
                speak("Sorry, something went wrong. Please try again.", mood="error")


# =========================
# Main Entry Point
# =========================

def main() -> None:
    list_mics()  # FIX: just call, don't print
    print("Welcome to Zero Vision Coding")
    speak("Welcome to Zero Vision Coding. I am Zero, your coding assistant.", mood="normal")

    mode = input("Type 't' for text chat or 's' for speech: ").strip().lower()

    if mode == "s":
        idx = input("Mic device index (blank for default): ").strip()
        device_index = int(idx) if idx else None
        speech_loop(device_index=device_index)
        return

    # Text chat loop
    while True:
        try:
            prompt = input("You: ").strip()
            if not prompt:
                continue

            # FIX: allow reset in text mode too
            if prompt.lower() == "reset":
                reset_conversation()
                print("Zero: Conversation reset.")
                continue

            print("Zero is thinking...")
            bot = chat(prompt)
            reply = bot.get("reply", "")
            print(f"Zero: {reply}")
            speak(reply, mood="normal")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            speak("Goodbye!", mood="normal")
            break
        except Exception as e:
            print(f"Error: {e}")
            speak("Something went wrong.", mood="error")


if __name__ == "__main__":
    main()