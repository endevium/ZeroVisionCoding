from __future__ import annotations

import os
import re
import time
import threading
from typing import TYPE_CHECKING

from .utils import extract_after_phrase, normalize_spoken_filename, extract_python_symbol_block, extract_snippet_around
from . import sfx

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

    def _spoken_line_number(value: str) -> int | None:
        value = value.lower().strip(" .,!?:;")
        if value.isdigit():
            return int(value)

        small_numbers = {
            "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
            "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
            "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
            "fourteen": 14, "fifteen": 15, "sixteen": 16,
            "seventeen": 17, "eighteen": 18, "nineteen": 19,
        }
        if value in small_numbers:
            return small_numbers[value]

        tens = {
            "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
            "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
        }
        parts = value.replace("-", " ").split()
        if len(parts) == 1 and parts[0] in tens:
            return tens[parts[0]]
        if len(parts) == 2 and parts[0] in tens and parts[1] in small_numbers:
            return tens[parts[0]] + small_numbers[parts[1]]
        return None

    if getattr(app, "_awaiting_line_number", False):
        line_number = _spoken_line_number(t)
        if line_number is not None:
            app._awaiting_line_number = False
            _handle_move_to_line(app, line_number)
            return

    explain_triggers: list[tuple[str, str]] = [
        ("explain function", "function"),
        ("explain the function", "function"),
        ("what does function", "function"),
        ("what does this function do", "function"),
        ("what does the function", "function"),
        ("tell me about the function", "function"),
        ("tell me about this function", "function"),
        ("what is this function for", "function"),
        ("describe the function", "function"),
        ("tell me what the function does", "function"),
        ("can you explain the function", "function"),
        ("can you explain this function", "function"),

        ("explain class", "class"),
        ("explain the class", "class"),
        ("what does the class do", "class"),
        ("what does this class do", "class"),
        ("tell me about the class", "class"),
        ("tell me about this class", "class"),
        ("can you explain the class", "class"),
        ("can you explain this class", "class"),

        ("explain variable", "variable"),
        ("explain the variable", "variable"),
        ("what is variable", "variable"),
        ("what is the variable", "variable"),
        ("what is this variable", "variable"),
        ("tell me about the variable", "variable"),
        ("what does the variable mean", "variable"),
        ("can you explain the variable", "variable"),
        ("can you explain this variable", "variable"),

        ("explain if", "conditional"),
        ("explain the if", "conditional"),
        ("explain conditional", "conditional"),
        ("explain the conditional", "conditional"),
        ("what does if", "conditional"),
        ("what does the if", "conditional"),
        ("what does the if statement do", "conditional"),
        ("what does this if do", "conditional"),
        ("tell me about the if statement", "conditional"),
        ("can you explain the if statement", "conditional"),

        ("explain for loop", "loop"),
        ("explain the for loop", "loop"),
        ("explain for", "loop"),
        ("what does for", "loop"),
        ("what does the for", "loop"),
        ("what does the for loop do", "loop"),
        ("what does this for do", "loop"),
        ("tell me about the for loop", "loop"),
        ("can you explain the for loop", "loop"),
        ("what does this for loop do", "loop"),

        ("explain while loop", "loop"),
        ("explain the while loop", "loop"),
        ("explain while", "loop"),
        ("what does while", "loop"),
        ("what does the while", "loop"),
        ("what does the while loop do", "loop"),
        ("what does this while do", "loop"),
        ("tell me about the while loop", "loop"),
        ("can you explain the while loop", "loop"),
        ("what does this while loop do", "loop"),

        ("explain try", "exception"),
        ("explain try except", "exception"),
        ("explain exception", "exception"),
        ("explain exception handling", "exception"),
        ("explain the try except block", "exception"),
        ("what does the try except block do", "exception"),
        ("what does this try do", "exception"),
        ("tell me about the try except block", "exception"),

        ("explain with", "context_manager"),
        ("explain the with statement", "context_manager"),
        ("explain with block", "context_manager"),
        ("explain context manager", "context_manager"),
        ("what does the with statement do", "context_manager"),
        ("what does this with do", "context_manager"),
        ("tell me about the context manager", "context_manager"),
        ("explain import", "import"),
        ("explain the import", "import"),
        ("what does the import do", "import"),
        ("what does this import do", "import"),
        ("tell me about the import", "import"),
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
    if any(phrase in t for phrase in (
        "fix it", "fix the error", "fix error", "fix code", "fix the code",
        "auto fix", "please fix", "fix this", "fix syntax", "fix this code",
        "fix my code", "fix the errors", "fix errors", "fix the syntax",
        "fix this error", "please fix this", "please fix the code",
        "correct the error", "correct the errors", "correct my code",
        "repair the code", "repair my code",
        "make the code work", "correct this program", "repair my program",
        "fix errors in my code", "please correct the syntax",
    )):
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

    # Cursor navigation
    move_to_line_match = re.search(
        r"\b(?:(?:move|go|jump)\s+(?:directly\s+)?to|take me\s+to|take\s+(?:the\s+)?cursor\s+to|put me on|navigate to|move the cursor to)\s+line\s+(.+?)\s*$",
        t,
    )
    if move_to_line_match:
        line_number = _spoken_line_number(move_to_line_match.group(1))
        if line_number is not None:
            app._awaiting_line_number = False
            _handle_move_to_line(app, line_number)
            return
    if any(phrase in t for phrase in (
        "move to line", "go to line", "jump to line",
        "move directly to line", "go directly to line",
        "jump directly to line", "take me to line",
        "take the cursor to line", "put me on line", "navigate to line",
        "move the cursor to line",
    )):
        app._awaiting_line_number = True
        app.interrupt_and_speak("Please say a line number. For example, move to line 3.")
        return

    if any(phrase in t for phrase in (
        "go to the editor", "go to editor", "focus the editor", "focus editor",
        "open the editor", "switch to the editor", "switch to editor",
        "take me to the editor",
        "put focus on the code editor", "move me into the editor",
        "focus the code area", "return to the editor",
        "place my focus in the editor",
    )):
        _handle_focus_command(app, "focus_editor", "editor")
        return

    if any(phrase in t for phrase in (
        "go to the terminal", "go to terminal", "focus the terminal", "focus terminal",
        "open the terminal", "switch to the terminal", "switch to terminal",
        "take me to the terminal", "go to the pseudoterminal",
        "go to pseudoterminal", "go to the pseudo terminal",
        "go to pseudo terminal", "focus the pseudoterminal",
        "focus pseudo terminal",
        "put focus on the terminal", "move me to the terminal",
        "switch to terminal", "work in the terminal",
    )):
        _handle_focus_command(app, "focus_terminal", "terminal")
        return

    # Navigation / readout
    if any(phrase in t for phrase in (
        "read the line", "read current line", "read this line",
        "read my current line", "tell me the current line",
        "tell me what's on this line", "what is on this line",
        "please read the line I am on", "read this line aloud",
        "what does the current line say", "speak the line under my cursor",
        "read the line under the cursor", "read aloud where my cursor is",
    )):
        app.speak_current_line_content()
        return

    if any(phrase in t for phrase in (
        "where am i", "current line", "what line am i on",
        "which line am i on", "where is my cursor", "cursor position",
        "what is my cursor position", "where is cursor",
        "tell me my cursor position",
        "where is the cursor", "what line is the cursor on",
        "give me my line number", "where am i in this code",
        "tell me the cursor location", "which line is selected",
    )):
        app.speak_current_line()
        return

    if any(phrase in t for phrase in (
        "what file is this", "what file am i in", "which file is this",
        "what is this file", "tell me the file name", "what is the file name",
    )):
        app.speak_active_file_name()
        return

    if any(phrase in t for phrase in (
        "read the whole thing", "read the whole code", "read all the code",
        "read the code", "read everything", "read the entire code",
        "tell me the code", "read my code",
        "read the complete file", "read this entire file aloud",
        "can you read all of this", "speak the whole program",
        "read the full source file", "hear the complete code",
        "read every line of the file",
    )):
        app.speak_full_editor()
        return

    if any(phrase in t for phrase in (
        "help", "i need help", "can you help me", "what can i say",
        "what commands can i use", "what can i tell you",
        "show me the commands", "show commands", "what can you do",
        "what are the commands",
        "list available commands", "tell me the available commands",
        "how do i use this assistant", "give me command help",
        "which voice commands are available",
    )):
        app.speak_help()
        return
    
    # Speech speed
    if any(phrase in t for phrase in (
        "speak faster", "faster speech", "speed up speech",
        "increase speech speed", "faster voice", "talk faster",
        "speak more quickly", "make your voice faster", "speed up your voice",
        "make your speech faster",
    )):
        app._speech_fast_mode = True
        # interrupt current and confirm
        app.interrupt_and_speak("Speech set to faster mode.")
        return

    if any(phrase in t for phrase in (
        "speak slower", "speak slow", "slower speech", "normal speed",
        "default speed", "decrease speech speed", "slower voice",
        "talk slower", "speak more slowly", "make your voice slower",
        "slow down your voice",
        "slow down your speech", "speak slowly", "set speech to normal speed",
        "return to normal speaking speed",
    )):
        app._speech_fast_mode = False
        app.interrupt_and_speak("Speech set to normal speed.")
        return

    # Save as
    save_as_phrases = (
        "save this file as", "save file as", "save as", "save this as",
        "save the file as", "save a copy as", "save a new copy as",
        "write this as", "make a copy of this file called",
        "save a duplicate as", "store this file under",
    )
    save_as_phrase = next((phrase for phrase in save_as_phrases if phrase in t), None)
    if save_as_phrase:
        remainder = extract_after_phrase(t, [save_as_phrase])
        file_name = normalize_spoken_filename(remainder)
        if not file_name:
            app.interrupt_and_speak("Please say a file name.")
            return
        _handle_save_as(app, file_name)
        return

    # Create a blank Python file
    create_file_phrases = (
        "create a new python file",
        "create new python file",
        "create a python file",
        "create python file",
        "make a new python file",
        "make new python file",
        "make a python file",
        "make python file",
        "create a new file",
        "create new file",
        "make a new file",
        "make new file",
        "new python file",
        "new file",
        "start a new python file",
        "start a new file",
        "create a new file called", "make a new file called",
        "please create a file named", "begin a new python file named",
        "open a new empty file",
    )
    create_file_phrase = next((phrase for phrase in create_file_phrases if phrase in t), None)
    if create_file_phrase:
        remainder = extract_after_phrase(t_raw, [create_file_phrase])
        remainder = remainder.removeprefix("named ").strip()
        file_name = normalize_spoken_filename(remainder or "untitled")
        _handle_create_new_file(app, file_name)
        return

    # Open saved file
    open_file_phrases = (
        "open file", "open the file", "open this file", "open saved file",
        "open the saved file", "load the file", "load saved file", "open my file",
        "bring up the file", "open the python file", "open my saved file",
        "load my file named", "please open file",
    )
    open_file_phrase = next((phrase for phrase in open_file_phrases if phrase in t), None)
    if open_file_phrase:
        remainder = extract_after_phrase(t, [open_file_phrase]).strip()
        name = normalize_spoken_filename(remainder)
        if not name:
            app.interrupt_and_speak("Please say the file name to open.")
            return
        _handle_open_saved_file(app, name)
        return

    # Run code
    if t_reply == "run":
        app.interrupt_and_speak("You can say 'run the code' to run the program.")
        return

    if any(phrase in t for phrase in (
        "run the code", "run code", "run the program", "run program",
        "run my program", "execute the code", "execute code",
        "execute the program", "execute program", "execute my program",
        "start the code", "start code", "start the program", "start program",
        "start my program", "start this program", "launch the code",
        "launch code", "launch the program", "launch program",
        "launch my program", "launch this program", "make the program start",
        "make this program start", "make the code run", "make this code run",
        "run my code", "run this code", "execute this program",
        "please run the current program", "i want to run the code",
    )):
        _handle_run_program(app)
        return

    # Save (current file)
    if (
        t_reply == "save"
        or any(phrase in t for phrase in (
            "save file", "save the file", "save this file", "save my file",
            "save work", "save my work", "save changes", "save my changes",
            "save the changes",
            "keep my changes", "keep the changes",
            "write the changes to disk", "can you save the file",
            "could you save what i changed", "i want to save",
            "store the current changes", "save everything in this file",
        ))
    ):
        _handle_save(app)
        return

    # Find errors
    if any(phrase in t for phrase in (
        "find errors in the code", "find error in the code",
        "find errors in code", "find error in code", "find errors", "find error",
        "check for errors", "check errors", "check my code for errors",
        "check the code for errors", "scan for errors", "scan the code for errors",
        "search for errors", "search the code for errors", "find bugs",
        "find a bug", "find the bugs", "check for bugs", "check my code for bugs",
        "check the code for bugs", "look for errors", "look for bugs",
        "are there any errors", "are there any bugs",
        "is there an error in my code",
        "find problems in the code", "look for problems in the code",
    )):
        app.find_errors_in_code()
        return

    # Analyze
    if any(phrase in t for phrase in (
        "analyze the code", "analyse the code", "analyze my code",
        "analyse my code", "analyze this code", "analyse this code",
        "analyze code", "analyse code", "analyze the program",
        "analyse the program", "examine the code", "examine my code",
        "inspect the code", "inspect my code",
        "tell me what is happening in the code",
        "please analyze this file", "can you analyze my program",
        "study this code", "give me an analysis of the code",
        "look deeply at my code",
    )):
        _handle_analyze(app)
        return

    # Close app
    if any(
        phrase in t
        for phrase in (
            "close the app",
            "close app",
            "close this app",
            "close the system",
            "close system",
            "exit the app",
            "exit app",
            "exit this app",
            "quit the app",
            "quit app",
            "quit this app",
            "exit application",
            "close application",
            "shut down the app",
            "shut down the application",
            "stop the app",
            "stop the application",
            "please close zero vision coding",
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
    if any(phrase in t for phrase in (
        "review my code", "review the code", "review code", "review this code",
        "review my program", "review the program", "check my code",
        "look over my code", "look at my code", "go over my code",
        "inspect my code", "give me a code review", "do a code review",
        "can you review my code", "can you look over my code",
        "please review this file", "tell me what you think of my code",
    )):
        _handle_code_review(app)
        return


    def _do_llm() -> None:
        try:
            # import and run llm code here (lazy import)
            from api.services import llm_service
            resp = llm_service.chat(text)
            reply = resp.get("reply") or "I couldn't generate a reply."
            is_unclear = resp.get("question_id") is None
        except Exception as e:
            reply = "Sorry, something went wrong."
            is_unclear = False

        # deliver result back on UI thread (so TTS/UI use is safe)
        def _deliver() -> None:
            try:
                if is_unclear:
                    app.speak_unclear(reply)
                else:
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


def _handle_move_to_line(app: "ZeroVisionAssistant", line_number: int) -> None:
    if line_number < 1:
        app.interrupt_and_speak("Line numbers start at 1.")
        return

    editor = app.client.editor()
    text = editor.get("text")
    if isinstance(text, str):
        last_line = text.count("\n") + 1
        if line_number > last_line:
            app.interrupt_and_speak(f"The last line is {last_line}.")
            return

    response = app.client.enqueue_command("move_to_line", {"line": line_number})
    command_id = response.get("id")
    if not command_id:
        app.interrupt_and_speak("I could not move the cursor.")
        return

    result = _wait_command_result(app, str(command_id), timeout_s=10.0)
    if result.get("ok"):
        app.interrupt_and_speak(f"Moved to line {line_number}.")
    else:
        message = str(result.get("message") or "").strip()
        app.interrupt_and_speak(f"I could not move to line {line_number}." + (f" {message}" if message else ""))


def _handle_focus_command(app: "ZeroVisionAssistant", command_type: str, name: str) -> None:
    response = app.client.enqueue_command(command_type, {})
    command_id = response.get("id")
    if not command_id:
        app.interrupt_and_speak(f"I could not go to the {name}.")
        return

    result = _wait_command_result(app, str(command_id), timeout_s=10.0)
    app.interrupt_and_speak(f"Moved to the {name}." if result.get("ok") else f"I could not go to the {name}.")


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


def _handle_create_new_file(app: "ZeroVisionAssistant", file_name: str) -> None:
    target_dir = app.get_active_file_dir()
    target_path = os.path.join(target_dir, file_name)

    if os.path.exists(target_path):
        app.interrupt_and_speak(f"{file_name} already exists. Please choose a different file name.")
        return

    app.interrupt_and_speak(f"Creating blank Python file {file_name}.")

    def _do() -> None:
        create_response = app.client.apply_file_content(target_path, "")
        create_id = create_response.get("id")
        if not create_id:
            app.after(0, lambda: app.interrupt_and_speak("I could not create the new file."))
            return

        create_result = _wait_command_result(app, str(create_id), timeout_s=12.0)
        if not create_result.get("ok"):
            app.after(0, lambda: app.interrupt_and_speak("I could not create the new file."))
            return

        open_response = app.client.enqueue_command("open_file", {"path": target_path})
        open_id = open_response.get("id")
        if not open_id:
            app.after(0, lambda: app.interrupt_and_speak("The file was created, but I could not open it."))
            return

        open_result = _wait_command_result(app, str(open_id), timeout_s=12.0)
        if open_result.get("ok"):
            app._saved_files[file_name.lower()] = target_path
            app.after(0, lambda: app.interrupt_and_speak(f"{file_name} is ready for coding."))
        else:
            app.after(0, lambda: app.interrupt_and_speak("The file was created, but I could not open it."))

    threading.Thread(target=_do, daemon=True).start()


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
    app.speech.set_paused(True)
    sfx.play_pop()
    app.interrupt_and_speak("Analyzing your code.")

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

    reminder_after_id = app.after(
        15000,
        lambda: app.interrupt_and_speak("Code analysis is still in progress."),
    )

    def _do() -> None:
        try:
            data = app.client.analyze_code(code, language=lang)
            narration = str(data.get("narration") or "").strip()
            steps = data.get("steps") or []
            result_text = (
                narration
                if narration
                else str(steps[0])
                if isinstance(steps, list) and steps
                else "I could not analyze the code."
            )
        except Exception:
            result_text = "I couldn't complete the code analysis. Please try again."

        def _deliver() -> None:
            app.after_cancel(reminder_after_id)
            app.speech.set_paused(False)
            sfx.play_ding()
            app.interrupt_and_speak(result_text)

        app.after(0, _deliver)

    threading.Thread(target=_do, daemon=True).start()

def _handle_chat(app: "ZeroVisionAssistant", user_text: str) -> None:
    try:
        from api.services import llm_service
        bot = llm_service.chat(user_text)
        reply = (bot.get("reply") if isinstance(bot, dict) else "") or ""
        reply = reply.strip()
        if reply:
            if isinstance(bot, dict) and bot.get("question_id") is None:
                app.speak_unclear(reply)
            else:
                app.speak(reply)
        else:
            app.speak_unclear(llm_service.unclear_response())
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

    app.speech.set_paused(True)
    app.interrupt_and_speak("Generating code review, please wait.")

    MAX_CHARS = 12000
    if len(editor_text) > MAX_CHARS:
        head = editor_text[: MAX_CHARS // 2]
        tail = editor_text[-MAX_CHARS // 2 :]
        code = head + "\n\n... truncated ...\n\n" + tail
    else:
        code = editor_text

    def _do() -> None:
        try:
            data = app.client.review_code(code, language=lang)
            narration = str(data.get("narration") or "").strip()
            overall_summary = str(data.get("overall_summary") or "").strip()
            final_assessment = str(data.get("final_assessment") or "").strip()
            issues = data.get("issues") or []
        except Exception:
            narration = ""
            overall_summary = ""
            final_assessment = "I couldn't complete the code review. Please try again."
            issues = []

        # Also run the same fast, reliable syntax/type check used by
        # "find errors", so a review can catch and offer to fix a real
        # bug even if the LLM's review missed it or was truncated.
        found_error = app.detect_code_error(editor_text, lang, editor_path)

        def _deliver() -> None:
            app.speech.set_paused(False)
            sfx.play_ding()
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