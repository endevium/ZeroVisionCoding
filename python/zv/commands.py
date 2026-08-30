from __future__ import annotations

import os
import time
import threading
from typing import TYPE_CHECKING

from .utils import extract_after_phrase, normalize_spoken_filename, extract_python_symbol_block, extract_snippet_around

if TYPE_CHECKING:
    from .app import ZeroVisionAssistant

def handle_text(app: "ZeroVisionAssistant", text: str) -> None:
    t_raw = (text or "").strip()
    t = t_raw.lower().strip()
    t_reply = t.strip(" .,!?:;")
    if not t:
        return

    def _is_yes(value: str) -> bool:
        value = value.strip(" .,!?:;")
        return value in ("yes", "yeah", "yep", "confirm", "correct", "looks good", "keep it", "save it", "save")

    def _is_no(value: str) -> bool:
        value = value.strip(" .,!?:;")
        return value in ("no", "nope", "revert", "undo", "wrong", "cancel", "take it back", "discard")

    explain_triggers: list[tuple[str, str]] = [
        ("explain function", "function"),
        ("explain the function", "function"),
        ("what does function", "function"),
        ("what does the function", "function"),

        ("explain class", "class"),
        ("explain the class", "class"),

        ("explain variable", "variable"),
        ("explain the variable", "variable"),
        ("what is variable", "variable"),
        ("what is the variable", "variable"),

        ("explain if", "conditional"),
        ("explain the if", "conditional"),
        ("explain conditional", "conditional"),
        ("explain the conditional", "conditional"),
        ("what does if", "conditional"),
        ("what does the if", "conditional"),

        ("explain for loop", "loop"),
        ("explain the for loop", "loop"),
        ("explain for", "loop"),
        ("what does for", "loop"),
        ("what does the for", "loop"),

        ("explain while loop", "loop"),
        ("explain the while loop", "loop"),
        ("explain while", "loop"),
        ("what does while", "loop"),
        ("what does the while", "loop"),

        ("explain try", "exception"),
        ("explain try except", "exception"),
        ("explain exception", "exception"),

        ("explain with", "context_manager"),
        ("explain import", "import"),
        ("explain the import", "import"),
    ]

    for trig, kind in explain_triggers:
        if trig in t:
            remainder = extract_after_phrase(t_raw, [trig]).strip()
            remainder = remainder.replace("to me", "").replace("please", "").strip()
            if kind in ("function", "class", "variable"):
                symbol = remainder.split()[0] if remainder else ""
            else:
                symbol = remainder if remainder else ""

            if not symbol:
                if kind in ("loop", "conditional", "exception", "context_manager", "import"):
                    app.interrupt_and_speak("Tell me which part to explain. For example, say explain if x is greater than 3.")
                else:
                    app.interrupt_and_speak("Tell me the name to explain.")
                return

            _handle_explain_symbol(app, symbol=symbol, kind=kind)
            return
        
    if getattr(app, "_pending_overwrite_path", None):
        _handle_pending_overwrite(app, t)
        return

    # Fixer
    if any(phrase in t for phrase in ("fix it", "fix the error", "fix error", "fix code", "fix the code", "auto fix", "please fix", "fix this", "fix syntax")):
        app.begin_fix_last_run_error()
        return

    if getattr(app, "_pending_fix_request", None):
        if _is_yes(t_reply) or t_reply in ("yes", "yeah", "yep", "go ahead"):
            app.begin_fix_last_run_error()
            return
        if _is_no(t_reply) or t_reply in ("no", "nope", "cancel", "stop"):
            app._pending_fix_request = None
            app.interrupt_and_speak("Okay. I will not change the code.")
            return

    # Fix confirmation
    if getattr(app, "_pending_fix_confirmation", None):
        if _is_yes(t_reply):
            app.confirm_fix()
            return
        if _is_no(t_reply):
            app.revert_fix()
            return

    # Navigation / readout
    if any(phrase in t for phrase in ("where am i", "current line", "where is my cursor", "cursor position", "where is cursor")):
        app.speak_current_line()
        return

    if "what file is this" in t:
        app.speak_active_file_name()
        return

    if "read the whole thing" in t or "read the code" in t:
        app.speak_full_editor()
        return

    if ("help" in t) or ("what can i say" in t):
        app.speak_help()
        return
    
    # Speech speed
    if any(phrase in t for phrase in ("speak faster", "faster speech", "speed up speech", "increase speech speed", "faster voice")):
        app._speech_fast_mode = True
        # interrupt current and confirm
        app.interrupt_and_speak("Speech set to faster mode.")
        return

    if any(phrase in t for phrase in ("speak slower", "speak slow", "normal speed", "default speed", "decrease speech speed", "slower voice")):
        app._speech_fast_mode = False
        app.interrupt_and_speak("Speech set to normal speed.")
        return

    # Save as
    if ("save this file as" in t) or ("save file as" in t) or ("save as" in t):
        remainder = extract_after_phrase(t, ["save this file as", "save file as", "save as"])
        file_name = normalize_spoken_filename(remainder)
        if not file_name:
            app.interrupt_and_speak("Please say a file name.")
            return
        _handle_save_as(app, file_name)
        return

    # Open saved file
    if "open file" in t:
        remainder = extract_after_phrase(t, ["open file"]).strip()
        name = normalize_spoken_filename(remainder)
        if not name:
            app.interrupt_and_speak("Please say the file name to open.")
            return
        _handle_open_saved_file(app, name)
        return

    # Run code
    if ("run the code" in t) or ("run code" in t) or ("run the program" in t) or ("run program" in t) or ("execute the code" in t) or ("execute code" in t) or ("execute the program" in t) or ("execute program" in t) or ("start the code" in t) or ("start code" in t) or ("start the program" in t) or ("start program" in t) or ("launch the code" in t) or ("launch code" in t) or ("launch the program" in t) or ("launch program" in t):
        _handle_run_program(app)
        return

    # Save (current file)
    if t.strip() == "save" or ("save file" in t) or ("save work" in t):
        _handle_save(app)
        return

    # Find errors
    if any(phrase in t for phrase in ("find errors in the code", "find error in the code", "find errors in code", "find error in code", "find errors", "find error", "check for errors", "check errors", "scan for errors", "search for errors", "find bugs", "check for bugs")):
        app.find_errors_in_code()
        return

    # Analyze
    if ("analyze the code" in t) or (("analyze" in t) or ("analyse" in t) and ("code" in t)):
        _handle_analyze(app)
        return

    # Close app
    if any(
        phrase in t
        for phrase in (
            "close the app",
            "close app",
            "close the system",
            "close system",
            "exit the app",
            "exit app",
            "quit the app",
            "quit app",
            "exit application",
            "close application",
        )
    ):
        app.interrupt_and_speak("Closing the application.")
        try:
            app.client.enqueue_command("close_extension", {})
        except Exception:
            pass
        app.after(200, app.on_close)
        return

    # Code reviewer
    if ("review my code" in t) or (("review" in t) and ("code" in t)):
        _handle_code_review(app)
        return
    
    # Tutorial Mode
    if ("enter tutorial mode" in t) or ("tutorial mode" in t) or (("tutorial") and (("mode") in t)):
        app.interrupt_and_speak("You have entered tutorial mode. This mode will help you learn how to use Zero Vision Coding and the fundamentals of Zero Vision Coding. Say 'list lessons' to hear the available lessons, or say a lesson name to begin. To exit tutorial mode, say 'exit tutorial mode'.")
        return
    
    # List of lessons
    if ("list lessons" in t) or ("what are the lessons" in t) or ("list all lessons" in t) or ("what are all the lessons" in t):
        app.interrupt_and_speak("The available lessons are 'Lesson 1: Get Started', 'Lesson 2: Braille Keyboard', 'Lesson 3: Voice Commands', 'Lesson 4: Python Basics', 'Lesson 5: Variables', 'Lesson 6: Conditionals', 'Lesson 7: Loops'")
        return
    
    # Exit Tutorial Mode
    if ("exit tutorial mode" in t) or ("exit tutorial" in t) or ("stop tutorial" in t) or ("end tutorial" in t):
        app.interrupt_and_speak("You have exited tutorial mode.")
        return


    def _do_llm() -> None:
        try:
            # import and run llm code here (lazy import)
            from api.services import llm_service
            resp = llm_service.chat(text)
            reply = resp.get("reply") or "I couldn't generate a reply."
        except Exception as e:
            reply = "Sorry, something went wrong."

        # deliver result back on UI thread (so TTS/UI use is safe)
        def _deliver() -> None:
            try:
                app.interrupt_and_speak(reply)
            except Exception:
                pass

        app.after(0, _deliver)

    threading.Thread(target=_do_llm, daemon=True).start()

def _handle_explain_symbol(app: "ZeroVisionAssistant", *, symbol: str, kind: str) -> None:
    app.interrupt_and_speak(f"Explaining {symbol}.")
    try:
        ed = app.client.editor()
        full = str(ed.get("text") or "")
        lang = str(ed.get("language") or "python")
    except Exception:
        full = ""
        lang = "python"

    snippet = None
    if lang.lower() in ("python", "py"):
        snippet = extract_python_symbol_block(full, symbol, kind=kind)
    if not snippet:
        snippet = extract_snippet_around(full, symbol, max_lines=90)

    snippet = snippet[:8000]

    def _do() -> None:
        data = app.client.explain_symbol(code=snippet, language=lang, symbol=symbol, kind=kind)
        summary = str(data.get("summary") or "").strip()
        details = data.get("details") or []

        def _deliver() -> None:
            app.interrupt_and_speak(summary or "I could not explain that symbol.")
            if isinstance(details, list):
                for d in details[:5]:
                    if isinstance(d, str) and d.strip():
                        app.speak(d.strip())

        app.after(0, _deliver)

    threading.Thread(target=_do, daemon=True).start()

def _wait_command_result(app: "ZeroVisionAssistant", cmd_id: str, timeout_s: float) -> dict:
    start = time.time()
    while time.time() - start < timeout_s:
        res = app.client.command_result(cmd_id)
        if "ok" in res:
            return res
        time.sleep(0.4)
    return {"ok": False, "message": "timeout"}


def _handle_pending_overwrite(app: "ZeroVisionAssistant", t: str) -> None:
    if ("yes" in t) or ("overwrite" in t):
        target_path = app._pending_overwrite_path
        target_name = app._pending_overwrite_name or os.path.basename(target_path)
        app._pending_overwrite_path = None
        app._pending_overwrite_name = None
        app.send_save_as_command(target_path, target_name)
        return

    if ("no" in t) or ("cancel" in t):
        app._pending_overwrite_path = None
        app._pending_overwrite_name = None
        app.interrupt_and_speak("Save canceled.")
        return

    app.interrupt_and_speak("Please say yes to overwrite or no to cancel.")


def _handle_save_as(app: "ZeroVisionAssistant", file_name: str) -> None:
    target_dir = app.get_active_file_dir()
    target_path = os.path.join(target_dir, file_name)

    if os.path.exists(target_path):
        app._pending_overwrite_path = target_path
        app._pending_overwrite_name = file_name
        app.interrupt_and_speak("This file already exists. Say yes to overwrite or no to cancel.")
        return

    app.send_save_as_command(target_path, file_name)


def _handle_open_saved_file(app: "ZeroVisionAssistant", name: str) -> None:
    target_path = app._saved_files.get(name.lower())
    if not target_path:
        app.interrupt_and_speak("I could not find that saved file.")
        return

    resp = app.client.enqueue_command("open_file", {"path": target_path})
    cmd_id = resp.get("id")
    if not cmd_id:
        app.interrupt_and_speak("Open failed.")
        return

    res = _wait_command_result(app, str(cmd_id), timeout_s=10.0)
    app.interrupt_and_speak("Open successful." if res.get("ok") else "Open failed.")


def _handle_run_program(app: "ZeroVisionAssistant") -> None:
    app._pending_fix_request = None
    try:
        app.client.terminal_reset()
    except Exception:
        pass
    
    resp = app.client.enqueue_command("run_program", {})
    cmd_id = resp.get("id")
    if not cmd_id:
        app.interrupt_and_speak("Could not enqueue run command.")
        return

    app.interrupt_and_speak("Running code, please wait.")
    app.start_terminal_reader()

    res = _wait_command_result(app, str(cmd_id), timeout_s=30.0)
    if res.get("ok"):
        app.speak("Run started. Reading terminal output.")
    else:
        msg = (res.get("message") or "").strip()
        app.interrupt_and_speak("Run failed." + ((" " + msg) if msg else ""))


def _handle_save(app: "ZeroVisionAssistant") -> None:
    file_name = app.get_active_file_name()
    app.interrupt_and_speak(f"Saving {file_name}")

    resp = app.client.enqueue_command("save_file", {})
    cmd_id = resp.get("id")
    if not cmd_id:
        app.interrupt_and_speak("Save failed.")
        return

    res = _wait_command_result(app, str(cmd_id), timeout_s=10.0)
    app.interrupt_and_speak("Save successful." if res.get("ok") else "Save failed.")


def _handle_analyze(app: "ZeroVisionAssistant") -> None:
    app.interrupt_and_speak("Analyzing code, please wait.")

    try:
        ed = app.client.editor()
        editor_text = str(ed.get("text") or "")
        lang = str(ed.get("language") or "python")
    except Exception:
        editor_text = ""
        lang = "python"

    # Cap input to protect RAM / llama.cpp
    MAX_CHARS = 12000
    if len(editor_text) > MAX_CHARS:
        head = editor_text[: MAX_CHARS // 2]
        tail = editor_text[-MAX_CHARS // 2 :]
        code = head + "\n\n... truncated ...\n\n" + tail
    else:
        code = editor_text

    def _do() -> None:
        data = app.client.analyze_code(code, language=lang)
        narration = str(data.get("narration") or "").strip()
        steps = data.get("steps") or []

        def _deliver() -> None:
            if narration:
                app.interrupt_and_speak(narration)
            elif isinstance(steps, list) and steps:
                app.interrupt_and_speak(str(steps[0]))
            else:
                app.interrupt_and_speak("I could not analyze the code.")

        app.after(0, _deliver)

    threading.Thread(target=_do, daemon=True).start()

def _handle_chat(app: "ZeroVisionAssistant", user_text: str) -> None:
    try:
        from api.services import llm_service
        bot = llm_service.chat(user_text)
        reply = (bot.get("reply") if isinstance(bot, dict) else "") or ""
        reply = reply.strip()
        if reply:
            app.speak(reply)
        else:
            app.speak("I'm sorry, I didn't quite get that.")
    except Exception:
        app.speak("Chat failed.")
    
def _handle_code_review(app: "ZeroVisionAssistant") -> None:
    try:
        ed = app.client.editor()
        editor_text = str(ed.get("text") or "")
        lang = str(ed.get("language") or "python")
        editor_path = str(ed.get("path") or "")
    except Exception:
        editor_text = ""
        lang = "python"
        editor_path = ""

    if not editor_text.strip():
        app.interrupt_and_speak("There is no code in the terminal.")
        return

    app.interrupt_and_speak("Generating code review, please wait.")

    MAX_CHARS = 12000
    if len(editor_text) > MAX_CHARS:
        head = editor_text[: MAX_CHARS // 2]
        tail = editor_text[-MAX_CHARS // 2 :]
        code = head + "\n\n... truncated ...\n\n" + tail
    else:
        code = editor_text

    def _do() -> None:
        data = app.client.review_code(code, language=lang)

        narration = str(data.get("narration") or "").strip()
        overall_summary = str(data.get("overall_summary") or "").strip()
        final_assessment = str(data.get("final_assessment") or "").strip()
        issues = data.get("issues") or []

        # Also run the same fast, reliable syntax/type check used by
        # "find errors", so a review can catch and offer to fix a real
        # bug even if the LLM's review missed it or was truncated.
        found_error = app.detect_code_error(editor_text, lang, editor_path)

        def _deliver() -> None:
            if narration:
                app.interrupt_and_speak(narration)
            elif overall_summary:
                app.interrupt_and_speak(overall_summary)
            elif issues:
                issue = issues[0]
                explanation = issue.get("explanation", "")
                recommendation = issue.get("recommendation", "")

                message = explanation
                if recommendation:
                    message += f" Recommendation: {recommendation}"

                app.interrupt_and_speak(message)
            elif final_assessment:
                app.interrupt_and_speak(final_assessment)
            else:
                app.interrupt_and_speak("I could not review the code.")

            if found_error:
                # Queue after whatever was just spoken, rather than
                # interrupting it.
                app.offer_fix_for_found_error(found_error, interrupt=False)

        app.after(0, _deliver)

    threading.Thread(target=_do, daemon=True).start()