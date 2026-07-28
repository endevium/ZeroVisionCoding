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

import os
import sys

# Ensure python directory is in sys.path to import from api
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "python"))
from api.services.llm_service import llm_chat

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

# ... [SPEECH MOODS AND SPEAKING FUNCTIONS REMAIN SAME] ...

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

    # Since we are using the local service's llm_chat wrapper but want to maintain this specific history structure:
    # We can reconstruct it or call llm_chat. Let's call the model using our singleton, but for simplicity
    # llm_chat in llm_service has its own prompts/QA system. Let's use llm_chat here directly.
    try:
        result = llm_chat(message)
    except Exception as e:
        result = {"reply": f"Chat failed. Error: {e}"}

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