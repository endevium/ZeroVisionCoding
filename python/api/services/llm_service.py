from __future__ import annotations
import json
import logging
import sys
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
MODEL_REPO = "Qwen/Qwen2.5-Coder-3B-Instruct-GGUF"
MODEL_FILENAME = "qwen2.5-coder-3b-instruct-q4_k_m.gguf"

_llm = None

def _models_dir() -> Path:
    """Return <repo_root>/models."""
    return Path(__file__).resolve().parents[3] / "models"

def _model_path() -> Path:
    return _models_dir() / MODEL_FILENAME


def _ensure_model_downloaded() -> Path:
    """Download the GGUF model from Hugging Face if it doesn't exist."""
    path = _model_path()
    if path.exists():
        return path
    logger.info("Model not found at %s — downloading from Hugging Face...", path)
    print(f"[llm_service] Downloading {MODEL_FILENAME} from {MODEL_REPO} (~1 GB)...")
    # pyrefly: ignore [missing-import]
    from huggingface_hub import hf_hub_download
    downloaded = hf_hub_download(
        repo_id=MODEL_REPO,
        filename=MODEL_FILENAME,
        local_dir=str(_models_dir()),
    )
    print(f"[llm_service] Model downloaded to {downloaded}")
    return Path(downloaded)


def _get_llm():
    """Lazy-load the llama.cpp model (singleton)."""
    global _llm
    if _llm is not None:
        return _llm
    model_file = _ensure_model_downloaded()
    # pyrefly: ignore [missing-import]
    from llama_cpp import Llama
    _llm = Llama(
        model_path=str(model_file),
        n_ctx=4096,
        n_threads=4,
        n_gpu_layers=0,  # CPU-only
        verbose=False,
    )
    print("[llm_service] Model loaded.")
    return _llm

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
    "You are a code explanation assistant designed for blind and visually-impaired programmers.\n"
    "Your goal is to convert code into clear, easy-to-follow spoken explanations.\n"

    "FIRST, silently analyze the code:\n"
    "- Determine the main purpose of the code\n"
    "- Identify key parts (functions, loops, conditions, variables)\n"
    "- Understand how data flows from start to end\n"
    "Do NOT output this analysis.\n"
    "- Do NOT use headings or labels like 'Steps:' or 'Narration:'.\n"

    "THEN, explain the code using these rules:\n"

    "Break the code into small logical steps based on behavior, not line-by-line reading.\n"
    "Each step must describe WHAT is happening, WHY it happens, and HOW it affects the flow.\n"

    "Group related lines into meaningful actions instead of explaining every line.\n"

    "Describe structure using spoken-friendly phrases like:\n"
    "- 'the code starts by...'\n"
    "- 'then it checks if...'\n"
    "- 'inside the loop...'\n"
    "- 'if the condition is true... otherwise...'\n"
    "- 'finally, it returns...'\n"

    "Track important variables and explain how their values change over time.\n"

    "Keep steps short (1 sentence each), but meaningful.\n"
    "Use simple language. Avoid jargon, or explain it briefly if necessary.\n"

    "After the steps, produce one narration paragraph that smoothly connects all steps.\n"
    "The narration must sound natural when spoken aloud, like explaining to a beginner.\n"

    "IMPORTANT RULES:\n"
    "- Do NOT read symbols or punctuation literally unless necessary.\n"
    "- Do NOT say 'line 1', 'line 2', or refer to code visually.\n"
    "- Do NOT repeat code.\n"
    "- Do NOT list syntax elements without explaining their purpose.\n"
    "- Focus on behavior, flow, and intent.\n"

    "Return ONLY valid JSON with this exact schema:\n"
    "{\n"
    '  "steps": [string, ...],\n'
    '  "narration": string\n'
    "}\n"

    "No markdown. No extra text."
)

''' FOR SPECIFIC ANALYSIS '''
EXPLAIN_SYMBOL_PROMPT = (
    "You are a code assistant for blind and visually-impaired programmers.\n"
    "Explain one specific symbol from the provided code snippet.\n"
    "The symbol can be a function, class, variable, or constant.\n"
    "- Do not use headings/labels like 'Function:', 'Class:', 'Variable:', 'Steps:'.\n"
    "Be short and concrete.\n"
    "If the snippet does not define the symbol, say it is not defined here and describe the most likely meaning from usage.\n"
    "Return ONLY valid JSON with this exact schema:\n"
    "{\n"
    '  "summary": string,\n'
    '  "details": [string, ...]\n'
    "}\n"
    "No markdown. No extra text."
)

''' FOR AI-ASSISTED DEBUGGING '''
FIX_PYTHON_ERROR_PROMPT = (
    "You are an expert Python code fixing assistant.\n"
    "You will be given a Python file and a traceback/error message.\n"
    "Fix the error with the smallest reasonable change.\n"
    "Before answering, verify the fix carefully against the traceback and the surrounding code.\n"
    "CRITICAL REQUIREMENT:\n"
    "- Do NOT output the entire file. Use the 'replacements' array to specify EXACT lines to search for and what to replace them with.\n"
    "- Your 'search' text MUST match the original code exactly, including leading spaces.\n"
    "- CRITICAL: The 'replace' text MUST be different from the 'search' text. Do not output a replacement that makes no changes.\n"
    "- Verify that every proposed replacement actually differs from the original code and modifies the behavior to address the issue.\n"
    "- Confirm that the modified code resolves the reported exception and compiles successfully.\n"
    "- You MUST preserve the original program logic. Do NOT rewrite, refactor, or optimize the code. Confine your replacements to the exact lines causing the error.\n"
    "- Keep 'search' blocks as small as possible—ideally a single line. Never replace an entire function if only one line is broken.\n"
    "- Avoid introducing new behavior unless it is absolutely necessary to fix the error.\n"
    "- If the error is an environment issue (like FileNotFoundError), leave the 'replacements' array empty and provide your recommendation in the 'summary' field.\n"
    "- If fixing an IndexError, explicitly reason about list lengths and loop bounds in your 'reasoning' field.\n"
    "- If fixing a KeyError, explicitly reason about key existence and proper dictionary handling.\n"
    "- If no valid fix can be generated from the traceback and code context, leave the 'replacements' array empty and explain why in the 'summary' field instead of claiming the error was fixed.\n"
    "- In a final self-check, compare each proposed replacement against the original code and discard any replacement that does not change behavior.\n"
    "Return ONLY valid JSON with this exact schema:\n"
    "{\n"
    '  "original_intent": string,\n'
    '  "reasoning": string,\n'
    '  "replacements": [\n'
    '    {\n'
    '      "search": string,\n'
    '      "replace": string\n'
    '    }\n'
    '  ],\n'
    '  "summary": string\n'
    "}\n"
    "No markdown fences around the JSON. No extra text."
)

''' FOR AI CODE REVIEW '''
PYTHON_CODE_REVIEW_PROMPT = (
    "You are a code reviewer for blind and visually-impaired programmers.\n"
    "Your job is to check whether the code works correctly, solves the problem it is meant to solve, "
    "meets its requirements without bugs, runs without crashing, is free of major slowdowns, and is easy to read and understand.\n\n"

    "IMPORTANT: Only report problems that actually exist in the code. Do not report an issue merely because "
    "the code matches a pattern from this checklist.\n"
    "Consider the purpose and context of the code before reporting an issue. A pattern is not automatically a bug.\n\n"

    "For example:\n"
    "- A function without a return statement is not automatically a bug. Only report it when the function is expected to return a value.\n"
    "- A print statement is not automatically a debugging statement. Only report it when there is strong evidence that it is temporary or diagnostic output.\n"
    "- A hard-coded number is not automatically a problem. Report it when its meaning is unclear and replacing it with a named constant would meaningfully improve the code.\n"
    "- Missing input validation is not automatically a problem. Report it only when invalid input can realistically cause incorrect behavior or a crash.\n"
    "- Shared or global state is not automatically a problem. Report it when the mutation can cause unexpected behavior or makes the code difficult to reason about.\n\n"

    "If the code is correct and clean, return an empty issues list.\n\n"

    "Before writing your review, carefully check the code for the following categories. "
    "Only report an issue when the code actually demonstrates the problem:\n\n"

    "BUGS AND CRASHES:\n"
    "- Will the code crash or produce incorrect results? Look for things like accessing a list position that does not exist, "
    "dividing by zero, using a variable that was never created, or returning an incorrect value.\n"
    "- Does a function that is expected to return a value actually return that value on every required execution path? "
    "Do not assume that every function needs a return statement. Functions whose purpose is to perform an action may correctly return nothing.\n"
    "- Is there code that can never execute? Report unreachable code only when execution genuinely cannot reach it, "
    "such as statements placed after an unconditional return, raise, break, or continue.\n"
    "- Can a loop fail to terminate? Report an infinite loop only when the loop's condition and updates show that execution "
    "can become permanently stuck. Do not assume that a loop is infinite simply because its stopping condition is not obvious.\n"
    "- Does a recursive function have a reachable base case? Report a problem only when the recursion can continue indefinitely "
    "because a required base case is missing or cannot be reached.\n"
    "- Does the code use 'is' or 'is not' when it appears to compare values such as strings, numbers, or other objects? "
    "In Python, 'is' checks whether two references point to the same object, while 'equals equals' compares their values. "
    "Report this only when 'is' is being used for value comparison. Do not report intentional identity checks, such as comparing a value with None.\n\n"

    "ERROR HANDLING:\n"
    "- Does the code use a bare 'except' or an overly broad exception handler? "
    "Report it when the broad handler can hide unexpected programming errors or make failures difficult to diagnose. "
    "Do not report it automatically when the broad handler is clearly intentional and appropriate for the surrounding code.\n"
    "- Does an exception handler silently ignore an error? "
    "Report it when the exception is caught and ignored without a clear reason, recovery behavior, or useful handling.\n\n"

    "PYTHON-SPECIFIC PITFALLS:\n"
    "- Does a function use a mutable object, such as a list or dictionary, as a default argument? "
    "Mutable default arguments are shared between calls and can cause state to persist unexpectedly. "
    "Report this as an issue unless the shared state is clearly intentional. "
    "The usual fix is to use None as the default and create the mutable object inside the function.\n"
    "- Does the code use a Python built-in name such as 'list', 'dict', 'str', 'input', 'id', 'type', or 'sum' "
    "for a variable, parameter, or function? Report this when the shadowed built-in could make later code confusing "
    "or prevent the built-in from being used normally. Do not claim that it will always break the program.\n"
    "- Does the code assign a value to a local variable that is never used afterward? "
    "Report this as a Low-severity cleanup issue when the assignment appears unnecessary. "
    "Do not report variables whose purpose is clear from their use in intentional Python patterns.\n\n"

    "READABILITY AND QUALITY:\n"
    "- Does the code contain a hard-coded number whose meaning is unclear and whose value may need to be changed independently? "
    "Report meaningful magic numbers, such as unexplained rates, limits, or configuration values. "
    "Do not report ordinary values such as 0, 1, -1, or small numbers used naturally in an algorithm.\n"
    "- Does the code contain print statements that appear to be temporary debugging output? "
    "Report a print statement only when there is strong evidence that it is diagnostic output, such as printing internal variables, "
    "intermediate calculations, loop counters, or debugging labels. "
    "Do not report normal user-facing output or printing that is clearly part of the function's intended purpose.\n"
    "- Does a function unexpectedly modify global or shared mutable state? "
    "Report this when the mutation can cause unintended side effects or make the function difficult to understand or test. "
    "Do not report global state merely because it exists.\n"
    "- Can invalid or unexpected input cause incorrect behavior, a crash, or an unsafe operation? "
    "Report missing validation only when validation is necessary for the function's expected inputs. "
    "Do not require validation for inputs that are already guaranteed by the surrounding code or problem requirements.\n"
    "- Would missing documentation make a non-trivial function difficult to understand or use? "
    "Report missing documentation only when it would meaningfully improve understanding. "
    "Do not require documentation for simple or self-explanatory functions.\n\n"

    "PERFORMANCE:\n"
    "- Does the code contain a performance problem that can meaningfully affect realistic input sizes? "
    "Pay attention to expensive operations repeated inside loops, unnecessary copying, repeated sorting, "
    "or algorithms with unnecessarily high time complexity.\n"
    "- For list construction, repeated concatenation can create unnecessary copies, but report it only when the loop "
    "can process enough elements for the inefficiency to matter. "
    "Do not report minor or theoretical performance differences in small or clearly bounded code.\n\n"

    "SEVERITY RULES:\n"
    "- Critical: The code WILL crash or produce wrong results every time it runs. "
    "Examples: missing return, off-by-one index error, infinite loop, division by zero with no check.\n"
    "- High: The code will crash or silently misbehave under common conditions. "
    "Examples: mutable default argument, bare except hiding real errors, using 'is' instead of 'equals equals' for value comparison.\n"
    "- Medium: The code works but has a clear quality or safety problem. "
    "Examples: missing input validation, shadowing a built-in name, no error handling for operations that can fail.\n"
    "- Low: The code works fine but could be cleaner or easier to understand. "
    "Examples: hard-coded numbers, leftover debug prints, missing documentation, unused variables.\n\n"

    "For each confirmed issue, include:\n"
    "- Where the problem occurs, using the function name, variable name, or a short description of the location.\n"
    "- What the problem is, explained clearly.\n"
    "- Why it is actually a problem in this code.\n"
    "- What can happen because of it and under what conditions.\n"
    "- How to fix it, with a short concrete example when useful.\n\n"

    "Do not invent consequences that are not supported by the code.\n\n"
    
    "Since the response will be read aloud by a screen reader:\n"
    "- Keep sentences short and clear.\n"
    "- Explain technical terms briefly when they are necessary.\n"
    "- Do not dump large blocks of rewritten code.\n"
    "- Refer to variables and functions using their exact names when identifying code.\n"
    "- Use natural spoken language when explaining code.\n"
    "- Do not unnecessarily repeat the same issue.\n\n"

    "Before producing the final JSON, perform a final verification:\n"
    "1. Remove any issue that is based only on a pattern and is not actually a problem in this code.\n"
    "2. Make sure every reported issue has evidence in the code.\n"
    "3. Make sure the explanation, impact, recommendation, and severity all refer to the same issue.\n"
    "4. Make sure severity reflects the actual impact and conditions described.\n"
    "5. If no real issues remain, return an empty issues list.\n\n"

    "Return ONLY valid JSON. Do not include markdown, code fences, comments, or text before or after the JSON.\n"
    "Use exactly this schema:\n"
    "{\n"
    '  "analysis": string,\n'
    '  "overall_summary": string,\n'
    '  "strengths": [string, ...],\n'
    '  "issues": [\n'
    '    {\n'
    '      "severity": "Critical|High|Medium|Low",\n'
    '      "location": string,\n'
    '      "explanation": string,\n'
    '      "impact": string,\n'
    '      "recommendation": string\n'
    '    }\n'
    '  ],\n'
    '  "final_assessment": string,\n'
    '  "narration": string\n'
    "}\n\n"

    "The 'analysis' field should briefly describe what the code is intended to do and the most important findings. "
    "Do not provide hidden reasoning or a long step-by-step chain of thought.\n"

    "The 'narration' field should be a short, natural spoken summary suitable for a screen reader. "
    "Mention the overall result and the most important issues, but do not repeat every issue word for word.\n\n"

    "No markdown. No extra text."
)


_QA_INDEX = None
_QA_LOAD_ERROR: str | None = None
_QA_ATTEMPTED = False

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]

def _load_qa_index() -> None:
    global _QA_INDEX, _QA_LOAD_ERROR
    try:
        from llm.qa_index import QAIndex 
        _QA_INDEX = QAIndex.load()
        _QA_LOAD_ERROR = None
        return
    except Exception as e1:
        try:
            import importlib.util
            qa_mod_path = _repo_root() / "llm" / "qa_index.py"
            spec = importlib.util.spec_from_file_location("zv_qa_index", str(qa_mod_path))
            if not spec or not spec.loader:
                raise RuntimeError("Cannot create import spec for qa_index.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            QAIndex = getattr(mod, "QAIndex")
            _QA_INDEX = QAIndex.load()
            _QA_LOAD_ERROR = None
            return
        except Exception as e2:
            _QA_INDEX = None
            _QA_LOAD_ERROR = f"QA index load failed: {e1} | {e2}"

def _ensure_qa_loaded() -> None:
    global _QA_ATTEMPTED
    if _QA_ATTEMPTED:
        return
    _QA_ATTEMPTED = True
    _load_qa_index()

def qa_status() -> dict:
    _ensure_qa_loaded()
    return {
        "loaded": bool(_QA_INDEX),
        "error": _QA_LOAD_ERROR,
    }

def _build_qa_context(query: str, k: int = 3) -> str:
    _ensure_qa_loaded()
    if not _QA_INDEX:
        return ""
    try:
        matches = _QA_INDEX.query(query, k=k)
    except Exception:
        return ""
    if not matches:
        return ""
    lines = ["Known Q/A (retrieved):"]
    for m in matches:
        lines.append(f"- question_id: {m.get('id')}")
        lines.append(f"  question: {m.get('question')}")
        lines.append(f"  answer: {m.get('answer')}")
    return "\n".join(lines)


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

    try:
        obj = json.loads(content)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    extracted = _extract_json_object(content)
    if extracted:
        try:
            obj = json.loads(extracted)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass

    return {}

def llm_chat(user_message: str, *, temperature: float = 0.3, num_predict: int = 120) -> dict:
    qa_ctx = _build_qa_context(user_message, k=3)
    combined_message = f"{user_message}\n\n{qa_ctx}" if qa_ctx else user_message

    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "user", "content": combined_message},
    ]

    try:
        result = _get_llm().create_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=num_predict,
        )
        raw = result["choices"][0]["message"]["content"]
    except Exception:
        return {"reply": "Chat failed. The local LLM service returned an error.", "question_id": None}
    data = _to_json(raw)

    reply = data.get("reply")
    qid = data.get("question_id")
    if isinstance(reply, str) and reply.strip():
        out = {"reply": reply}
        out["question_id"] = qid if (isinstance(qid, str) and qid.strip()) else None
        return out

    return {"reply": _strip_code_fences(raw).strip() or "No response.", "question_id": None}

def llm_analyze(code: str, language: str, *, temperature: float = 0.1, num_predict: int = 1500) -> dict:
    language = (language or "python").lower()
    if language in ("python", "py"):
        outline = _python_outline(code)
        snippet = (code or "")[:4000]
        code_for_llm = f"OUTLINE:\n{outline}\n\nSNIPPET:\n{snippet}"
    else:
        code_for_llm = (code or "")[:8000]

    messages = [
        {"role": "system", "content": ANALYZE_SYSTEM_PROMPT},
        {"role": "user", "content": f"Language: {language}\n\nCode:\n{code_for_llm}"},
    ]

    try:
        result = _get_llm().create_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=num_predict,
        )
        raw = result["choices"][0]["message"]["content"]
    except Exception as e:
        return {"steps": [], "narration": "Code analysis failed. The local LLM service returned an error."}
    data = _to_json(raw)
    if not data:
        text = _strip_code_fences(raw).strip()
        if len(text) > 1400:
            text = text[:1400] + " ..."
        return {"steps": [], "narration": text or "I could not parse the analysis output."}

    steps = data.get("steps")
    narration = data.get("narration")

    if not isinstance(steps, list) or not all(isinstance(x, str) for x in steps):
        steps = []

    if not isinstance(narration, str):
        narration = ""

    return {"steps": steps, "narration": narration}

def llm_explain_symbol(code: str, language: str, symbol: str, kind: str = "") -> dict:
    messages = [
        {"role": "system", "content": EXPLAIN_SYMBOL_PROMPT},
        {
            "role": "user",
            "content": (
                f"Language: {language}\n"
                f"Requested symbol: {symbol}\n"
                f"Kind (optional): {kind}\n\n"
                f"Code snippet:\n{code}\n"
            ),
        },
    ]

    try:
        result = _get_llm().create_chat_completion(
            messages=messages,
            temperature=0.2,
            max_tokens=320,
        )
        raw = result["choices"][0]["message"]["content"]
    except Exception:
        return {"summary": "Explain failed. The local LLM service returned an error.", "details": []}

    data = _to_json(raw)
    summary = data.get("summary")
    details = data.get("details")
    if not isinstance(summary, str):
        summary = _strip_code_fences(raw).strip() or "No response."
    if not isinstance(details, list) or not all(isinstance(x, str) for x in details):
        details = []
    return {"summary": summary, "details": details}

def _apply_code_replacement(code: str, search: str, replace: str, err_line: Optional[int] = None) -> tuple[str, bool]:
    code_norm = code.replace("\r\n", "\n")
    search_norm = search.replace("\r\n", "\n").strip("\r\n")
    replace_norm = replace.replace("\r\n", "\n").strip("\r\n")

    if not search_norm or search_norm == replace_norm:
        return code, False

    # 1. Exact match
    if search_norm in code_norm:
        return code_norm.replace(search_norm, replace_norm, 1), True

    lines = code_norm.split("\n")
    search_clean = search_norm.strip()
    replace_clean = replace_norm.strip()

    # 2. Stripped line match
    for i, line in enumerate(lines):
        if line.strip() == search_clean and search_clean != "":
            indent = line[: len(line) - len(line.lstrip())]
            lines[i] = indent + replace_clean
            return "\n".join(lines), True

    # 3. Line-index fallback if err_line available
    if err_line is not None and 1 <= err_line <= len(lines):
        idx = err_line - 1
        target_line = lines[idx]
        if search_clean in target_line or target_line.strip() in search_clean or len(search_clean) < 3:
            indent = target_line[: len(target_line) - len(target_line.lstrip())]
            lines[idx] = indent + replace_clean
            return "\n".join(lines), True

    return code, False


def _fix_common_syntax_typo(code: str, err_line: Optional[int]) -> tuple[str, bool]:
    import re

    code_norm = code.replace("\r\n", "\n")
    lines = code_norm.split("\n")

    target_indices = [err_line - 1] if (err_line is not None and 1 <= err_line <= len(lines)) else range(len(lines))

    for idx in target_indices:
        line = lines[idx]
        # Fix common operator typos in assignments: =/, =m, =+, =*, =-, =@, =%
        new_line = re.sub(r'=\s*[/m+*\-@%]\s*', '= ', line)
        if new_line != line:
            lines[idx] = new_line
            return "\n".join(lines), True

    return code, False


def llm_fix_python_error(*, code: str, error: str, temperature: float = 0.0, num_predict: int = 1000) -> dict:
    import ast

    current_code = code.replace("\r\n", "\n")
    current_error = error
    last_summary = ""
    total_applied = False
    all_summaries = []

    for _pass_idx in range(3):
        # Extract line number from current_error if present
        err_line = None
        import re
        m = re.search(r'line\s+(\d+)', current_error, re.IGNORECASE)
        if m:
            try:
                err_line = int(m.group(1))
            except Exception:
                err_line = None

        messages = [
            {"role": "system", "content": FIX_PYTHON_ERROR_PROMPT},
            {
                "role": "user",
                "content": (
                    "Python file content:\n"
                    f"{current_code}\n\n"
                    "Traceback / error:\n"
                    f"{current_error}\n"
                ),
            },
        ]

        raw = ""
        try:
            result = _get_llm().create_chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=num_predict,
            )
            raw = result["choices"][0]["message"]["content"]
        except Exception:
            pass

        applied_this_pass = False
        if raw:
            data = _to_json(raw)
            summary = str(data.get("summary") or "").strip()
            if summary:
                last_summary = summary
                if summary not in all_summaries:
                    all_summaries.append(summary)
            replacements = data.get("replacements")

            if isinstance(replacements, list):
                for rep in replacements:
                    if isinstance(rep, dict):
                        search = rep.get("search", "")
                        replace = rep.get("replace", "")
                        if search and isinstance(search, str) and isinstance(replace, str):
                            new_code, ok = _apply_code_replacement(current_code, search, replace, err_line=err_line)
                            if ok:
                                current_code = new_code
                                applied_this_pass = True
                                total_applied = True

        # Fallback: try deterministic syntax typo repair if LLM replacement didn't apply
        if not applied_this_pass:
            new_code, ok = _fix_common_syntax_typo(current_code, err_line)
            if ok:
                current_code = new_code
                applied_this_pass = True
                total_applied = True
                if not last_summary:
                    last_summary = f"Fixed syntax typo at line {err_line or 1}."
                if last_summary not in all_summaries:
                    all_summaries.append(last_summary)

        if not applied_this_pass:
            break

        # Check if current_code is now valid python
        try:
            ast.parse(current_code)
            # All syntax errors resolved!
            break
        except SyntaxError as se:
            err_line = se.lineno or 1
            err_col = se.offset or 1
            err_msg = se.msg or "syntax error"
            current_error = f"SyntaxError: {err_msg} at line {err_line}, column {err_col}"

    if not total_applied or current_code.strip() == code.strip():
        return {"content": "", "summary": last_summary or "I could not generate a fix for the file."}

    final_summary = " ".join(all_summaries) if all_summaries else (last_summary or "Applied fixes to resolve code errors.")
    return {"content": current_code, "summary": final_summary}

def _strip_code_fences(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("```"):
        lines = s.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        s = "\n".join(lines).strip()
    return s


def _python_ast_dump(code: str) -> str:
    import ast

    tree = ast.parse(code or "")
    return ast.dump(tree, include_attributes=False)


def _python_static_review_issues(code: str) -> list[dict]:
    import ast

    code = code or ""
    issues: list[dict] = []

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        issues.append({
            "severity": "Critical",
            "location": f"line {getattr(exc, 'lineno', '?')}",
            "explanation": f"Python cannot parse this file: {exc.msg}.",
            "impact": "The code will not run at all until the syntax error is fixed.",
            "recommendation": "Correct the syntax error reported by Python and run the file again.",
        })
        return issues

    env: dict[str, str] = {}

    def infer_type(node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return "str"
            if isinstance(node.value, bool):
                return "bool"
            if isinstance(node.value, int):
                return "int"
            if isinstance(node.value, float):
                return "float"
            return None
        if isinstance(node, ast.Name):
            return env.get(node.id)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left_type = infer_type(node.left)
            right_type = infer_type(node.right)
            if left_type == right_type:
                return left_type
            if {left_type, right_type} <= {"int", "float"}:
                return "float" if "float" in (left_type, right_type) else "int"
            if "str" in (left_type, right_type) and ("int" in (left_type, right_type) or "float" in (left_type, right_type) or "bool" in (left_type, right_type)):
                return "type_error"
        return None

    class Collector(ast.NodeVisitor):
        def visit_Assign(self, node: ast.Assign) -> None:
            value_type = infer_type(node.value)
            if value_type and value_type != "type_error":
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        env[target.id] = value_type
            self.generic_visit(node)

        def visit_BinOp(self, node: ast.BinOp) -> None:
            if isinstance(node.op, ast.Add):
                left_type = infer_type(node.left)
                right_type = infer_type(node.right)
                if {left_type, right_type} == {"str", "int"} or {left_type, right_type} == {"str", "float"} or {left_type, right_type} == {"str", "bool"}:
                    snippet = ast.get_source_segment(code, node) or "x + y"
                    issues.append({
                        "severity": "High",
                        "location": snippet,
                        "explanation": "This addition mixes a string with a number, so Python will raise a TypeError.",
                        "impact": "The program will crash when it reaches this expression.",
                        "recommendation": "Convert the number to a string, or change the logic so you are not adding incompatible types.",
                    })
            self.generic_visit(node)

    Collector().visit(tree)
    return issues

def chat(message: str) -> dict:
    _ensure_qa_loaded()
    msg = (message or "").strip()
    if not msg:
        return {"reply": "I'm sorry, I didn't quite get that, can you repeat?", "question_id": None}

    if _QA_INDEX:
        try:
            matches = _QA_INDEX.query(msg, k=1)
            if matches:
                best = matches[0]
                score = float(best.get("score", 0.0))
                answer = (best.get("answer") or "").strip()
                qid = (best.get("id") or "").strip()

                wc = len(msg.split())
                threshold = 0.60 if wc <= 2 else 0.72 
                if answer and score >= threshold:
                    return {"reply": answer, "question_id": qid or None}
        except Exception:
            pass

    return {"reply": "I'm sorry, I didn't quite get that, can you repeat?", "question_id": None}

def _python_outline(code: str) -> str:
    """
    Returns a compact outline of Python code so the LLM can analyze larger files cheaply.
    """
    code = code or ""
    try:
        import ast
        tree = ast.parse(code)
    except Exception:
        # fallback: just clip
        return code[:6000]

    lines: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            lines.append(f"class {node.name}:")
            for b in node.body:
                if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = []
                    for a in b.args.args:
                        args.append(a.arg)
                    lines.append(f"  def {b.name}({', '.join(args)}):")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            lines.append(f"def {node.name}({', '.join(args)}):")
        elif isinstance(node, ast.Import):
            for n in node.names:
                lines.append(f"import {n.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            names = ", ".join(n.name for n in node.names)
            lines.append(f"from {mod} import {names}")
        elif isinstance(node, ast.Assign):
            # only simple names
            targets = []
            for t in node.targets:
                if isinstance(t, ast.Name):
                    targets.append(t.id)
            if targets:
                lines.append(f"{', '.join(targets)} = ...")

    return "\n".join(lines).strip()

def llm_code_review(code: str, language: str, *, temperature: float = 0.0, num_predict: int = 1500) -> dict:
    # TODO: Fix narrator saying the _ or other symbols
    language = (language or "python").lower()
    outline = _python_outline(code)
    snippet = (code or "")[:6000]
    code_for_llm = f"OUTLINE:\n{outline}\n\nSNIPPET:\n{snippet}"

    messages = [
        {"role": "system", "content": PYTHON_CODE_REVIEW_PROMPT},
        {
            "role": "user",
            "content": f"Language: {language}\n\nCode:\n{code_for_llm}",
        },
    ]

    empty_response = {
        "overall_summary": "",
        "strengths": [],
        "issues": [],
        "rating": 0,
        "rating_explanation": "",
        "final_assessment": "",
        "narration": "",
    }

    try:
        result = _get_llm().create_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=num_predict,
        )
        raw = result["choices"][0]["message"]["content"]
    except Exception:
        empty_response["narration"] = (
            "Failed to generate review. The local LLM service returned an error."
        )
        return empty_response

    data = _to_json(raw)

    if not data:
        text = _strip_code_fences(raw).strip()
        if len(text) > 1400:
            text = text[:1400] + " ..."

        empty_response["narration"] = (
            text or "I could not parse the code review output."
        )
        return empty_response

    response = {
        "overall_summary": data.get("overall_summary", ""),
        "strengths": data.get("strengths", []),
        "issues": data.get("issues", []),
        "rating": data.get("rating", 0),
        "rating_explanation": data.get("rating_explanation", ""),
        "final_assessment": data.get("final_assessment", ""),
        "narration": data.get("narration", ""),
    }

    # Clean underscores from top-level text fields to protect TTS output
    # Validate and clamp rating
    try:
        response["rating"] = max(1, min(10, int(response["rating"])))
    except (TypeError, ValueError):
        response["rating"] = 0
    if not isinstance(response["rating_explanation"], str):
        response["rating_explanation"] = ""

    # Clean underscores from top-level text fields to protect TTS output
    for key in ("overall_summary", "final_assessment", "narration", "rating_explanation"):
        if isinstance(response[key], str):
            response[key] = response[key].replace("overall_summary", "overall summary").replace("final_assessment", "final assessment").replace("_", " ")

    # Validate strengths
    if not (
        isinstance(response["strengths"], list)
        and all(isinstance(x, str) for x in response["strengths"])
    ):
        response["strengths"] = []

    if not isinstance(response["issues"], list):
        response["issues"] = []

    valid_issues = []
    for issue in response["issues"]:
        if not isinstance(issue, dict):
            continue

        # Clean underscores from issue text fields to protect TTS output
        cleaned_issue = {
            "severity": str(issue.get("severity", "Low")),
            "location": str(issue.get("location", "")),
            "explanation": str(issue.get("explanation", "")),
            "impact": str(issue.get("impact", "")),
            "recommendation": str(issue.get("recommendation", "")),
        }
        for k in ("location", "explanation", "impact", "recommendation"):
            cleaned_issue[k] = cleaned_issue[k].replace("overall_summary", "overall summary").replace("final_assessment", "final assessment").replace("_", " ")
        valid_issues.append(cleaned_issue)

    response["issues"] = valid_issues

    static_issues = _python_static_review_issues(code) if language in ("python", "py") else []
    if static_issues:
        seen = {(issue.get("location", ""), issue.get("explanation", "")) for issue in response["issues"]}
        for issue in static_issues:
            key = (issue.get("location", ""), issue.get("explanation", ""))
            if key not in seen:
                response["issues"].insert(0, issue)
                seen.add(key)

        if not response["overall_summary"] or "works well" in response["overall_summary"].lower() or "no issues" in response["overall_summary"].lower():
            response["overall_summary"] = "I found at least one likely runtime problem in the code."
        if not response["final_assessment"] or "works well" in response["final_assessment"].lower() or "no issues" in response["final_assessment"].lower():
            response["final_assessment"] = "The code is not correct as written."
        if not response["narration"] or "works well" in response["narration"].lower() or "no issues" in response["narration"].lower():
            first_issue = response["issues"][0]
            response["narration"] = f"I found a likely problem at {first_issue['location']}: {first_issue['explanation']}"

    for key in (
        "overall_summary",
        "final_assessment",
        "narration",
    ):
        if not isinstance(response[key], str):
            response[key] = ""

    return response