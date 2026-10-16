from __future__ import annotations
import json
import logging
import random
import sys
import os
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_UNCLEAR_RESPONSES = [
    "Sorry, I didn't quite catch that. Can you repeat?",
    "Could you say that again?",
    "Sorry, can you repeat that?",
    "I didn't understand. Could you explain it again?",
    "Could you repeat that one more time?",
    "Sorry, I missed that. Can you say it again?",
    "Can you go over that again?",
    "Could you clarify that for me?",
    "I'm not sure I understood. Can you explain it again?",
    "Sorry, I didn't hear you clearly. Can you repeat that?",
]

_last_unclear_response = None
_UNCLEAR_RESPONSE_LOCK = threading.Lock()


def unclear_response() -> str:
    """Return exactly ONE randomly selected clarification response."""
    global _last_unclear_response

    with _UNCLEAR_RESPONSE_LOCK:
        choices = [
            response
            for response in _UNCLEAR_RESPONSES
            if response != _last_unclear_response
        ]

        selected = random.choice(choices)
        _last_unclear_response = selected

        return selected

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
MODEL_REPO = "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
MODEL_FILENAME = "qwen2.5-coder-7b-instruct-q4_k_m.gguf"

_llm = None
_LLM_LOCK = threading.Lock()

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
    with _LLM_LOCK:
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


def _chat_completion(**kwargs):
    """Thread-safe chat completion using llama.cpp singleton."""
    llm = _get_llm()
    with _LLM_LOCK:
        return llm.create_chat_completion(**kwargs)


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
    "You are an expert code explanation and error detection assistant for blind and visually-impaired programmers.\n"
    "Your highest priority is to rigorously detect any semantic, calculation, or logical errors in the code, and explain the code clearly.\n\n"

    "FIRST: RIGOROUSLY AUDIT FOR SEMANTIC AND LOGICAL ERRORS:\n"
    "Carefully inspect calculations, formulas, conditions, loops, and control flow for semantic and logical bugs that cause wrong results or unintended behavior even when the code runs without syntax crashes. Thoroughly check:\n"
    "- Calculation & formula errors: adding discounts/deductions/coupons instead of subtracting them, subtracting taxes/tips/fees/surcharges instead of adding them, multiplying instead of dividing, inverted percentages, or incorrect formulas.\n"
    "- Operator precedence errors: missing parentheses in calculations like averages ('a + b / 2' instead of '(a + b) / 2') or complex math.\n"
    "- Average and aggregation bugs: dividing by the wrong number of terms (e.g. dividing by 2 when 3 terms are added), dividing inside an accumulation loop instead of after summing, or wrong count.\n"
    "- Accumulator bugs: initializing multiplication or factorial accumulators to 0 instead of 1 (resulting in 0), or resetting sum/count accumulators inside loop bodies instead of before the loop.\n"
    "- Loop logic bugs: returning on the first iteration of a loop unconditionally instead of processing all elements, or off-by-one errors in range/indexing.\n"
    "- Min/Max logic errors: inverted comparisons when searching for maximum ('<' instead of '>') or minimum ('>' instead of '<').\n"
    "- Condition & boolean logic bugs: using 'and' instead of 'or' (or vice versa), 'if x == 1 or 2' (comparing with truthy literal constant), conditions like 'x != \"a\" or x != \"b\"' which are always True, contradictory conditions like 'x > 10 and x < 5', inverted comparison operators ('<' instead of '>', '==' instead of '!='), or identity check 'is' instead of '==' on literals.\n"
    "- State & variable bugs: overwriting a variable before reading it (like 'a = b; b = a'), using the wrong variable in a calculation, or swapping arguments.\n\n"

    "For each confirmed semantic or logical problem:\n"
    "- Provide the 1-based line number where the problem occurs.\n"
    "- Provide a concise, spoken-friendly explanation of why the calculation or logic is wrong and what it should be.\n"
    "- Set 'kind' to 'logical' or 'semantic'.\n"
    "If the code has no semantic or logical errors, 'issues' MUST be an empty array [].\n\n"

    "SECOND: EXPLAIN THE CODE:\n"
    "- Break the code into small logical steps based on behavior, not line-by-line reading.\n"
    "- Each step must describe WHAT is happening, WHY it happens, and HOW it affects the flow.\n"
    "- Group related lines into meaningful actions instead of explaining every line.\n"
    "- Describe structure using spoken-friendly phrases like 'the code starts by...', 'then it checks if...', 'inside the loop...'.\n"
    "- Keep steps short (1 sentence each), but meaningful.\n"
    "- After the steps, produce one narration paragraph that smoothly connects all steps.\n"
    "- If any issue was found, clearly explain the mistake in the narration so the user is immediately aware of it.\n\n"

    "IMPORTANT RULES:\n"
    "- Do NOT read symbols or punctuation literally unless necessary.\n"
    "- In 'steps' and 'narration', do NOT say 'line 1', 'line 2', or refer to code visually.\n"
    "- Do NOT repeat code.\n"
    "- Do NOT list syntax elements without explaining their purpose.\n"
    "- Focus on behavior, flow, and intent.\n\n"

    "Return ONLY valid JSON with this exact schema (issues first):\n"
    "{\n"
    '  "issues": [{"line": number, "message": string, "kind": "logical" | "semantic"}],\n'
    '  "steps": [string, ...],\n'
    '  "narration": string\n'
    "}\n\n"

    "No markdown. No extra text."
)

''' 
FOR FAST SEMANTIC CHECK (RUN CODE / VERIFICATION)
'''
SEMANTIC_CHECK_SYSTEM_PROMPT = (
    "You are an expert Python logic and semantic error auditor for visually impaired programmers.\n"
    "Your ONLY job is to identify potential semantic, calculation, or logical errors that cause incorrect results or behavior.\n"
    "Check specifically for:\n"
    "- Calculations: incorrect operators, formulas, discounts, taxes, tips, fees, and percentage calculations\n"
    "- Precedence: missing parentheses or incorrect operator precedence\n"
    "- Aggregations: incorrect counts, averages, totals, or division by the wrong value\n"
    "- Accumulators: incorrect initialization, unintended resets, or missing updates\n"
    "- Inverted logic: incorrect comparisons, min/max selection, or even/odd checks\n"
    "- Loop bugs: off-by-one bounds, incorrect iteration, premature returns, or skipped items\n"
    "- Conditions: contradictory conditions, incorrect Boolean operators, or conditions that are always true or false\n"
    "- Variable usage: using the wrong variable, stale values, or incorrect assignments\n"
    "- Return behavior: returning an intermediate or incorrect value\n"
    "- Indexing and collections: accessing the wrong element, incorrect filtering, or processing only part of a collection\n"
    "- Function calls: passing arguments in the wrong order when this causes incorrect behavior\n"
    "- Boundary cases: incorrect behavior for empty collections, single elements, zero, negative values, or threshold values\n"
    "- Data flow: using a value before the intended update or failing to propagate a calculated result\n\n"
    "Only report an issue when the code provides reasonable evidence of a potential error. Do not assume that a valid operator, variable name, or programming style is incorrect without supporting evidence.\n"
    "If an intended behavior or requirement is provided, compare the code against it. If the intended behavior is unclear, do not invent requirements; report only clearly supported issues.\n"
    "Do not report syntax errors, formatting preferences, or ordinary code-quality suggestions unless they directly cause incorrect behavior.\n\n"
    "Return ONLY valid JSON with this exact schema:\n"
    "{\n"
    '  "issues": [{"line": number, "message": string, "kind": "logical" | "semantic"}]\n'
    "}\n"
    "Use the relevant line number for each issue. If no supported issues are found, return exactly:\n"
    '{"issues": []}\n'
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
    "You are an expert Python debugging assistant.\n"
    "You will receive Python code and an error report. The report may be a Python traceback, a syntax error, "
    "a runtime error, a static type-checker diagnostic such as Pyright output, or a logical or semantic error report "
    "(such as an incorrect calculation, wrong operator, or flawed condition).\n"
    "Identify the exact line causing the error and propose the smallest possible fix. For a type-checker diagnostic, "
    "fix the incompatible expression or annotation while preserving the intended behavior. For a logical or semantic "
    "error, correct the calculation or logic to match the intended behavior.\n"
    "\n"
    "RULES:\n"
    "- Preserve the original program structure and intended behavior.\n"
    "- Do not rewrite or refactor unrelated code.\n"
    "- Make only the changes necessary to fix the reported error.\n"
    "- Keep each search block as small as possible, preferably one line.\n"
    "- The 'search' text must exactly match the original code.\n"
    "- The 'replace' text must be different from the search text.\n"
    "- If the problem is an environment issue that cannot be fixed by changing the code, return an empty replacements array.\n"
    "- If there is not enough information to safely determine a fix, return an empty replacements array.\n"
    "\n"
    "Return ONLY valid JSON:\n"
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
    "No markdown. No extra text."
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
        result = _chat_completion(
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

def llm_analyze(code: str, language: str, *, temperature: float = 0.1, num_predict: int = 1200, seed: int = 42) -> dict:
    language = (language or "python").lower()
    if language in ("python", "py"):
        if len(code or "") <= 5000:
            code_for_llm = code or ""
        else:
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
        result = _chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=num_predict,
        )
        raw = result["choices"][0]["message"]["content"]
    except Exception as e:
        return {
            "steps": [],
            "narration": "Code analysis failed. The local LLM service returned an error.",
            "issues": [],
        }
    data = _to_json(raw)
    if not data:
        text = _strip_code_fences(raw).strip()
        if len(text) > 1400:
            text = text[:1400] + " ..."
        return {"steps": [], "narration": text or "I could not parse the analysis output.", "issues": []}

    steps = data.get("steps")
    narration = data.get("narration")

    if not isinstance(steps, list) or not all(isinstance(x, str) for x in steps):
        steps = []

    if not isinstance(narration, str):
        narration = ""

    raw_issues = data.get("issues")
    issues = []
    if isinstance(raw_issues, list):
        for issue in raw_issues:
            if not isinstance(issue, dict):
                continue
            try:
                line = int(issue.get("line", 1))
            except (TypeError, ValueError):
                line = 1
            message = issue.get("message")
            kind = issue.get("kind")
            if isinstance(message, str) and message.strip():
                issues.append({
                    "line": max(1, line),
                    "message": message.strip(),
                    "kind": kind if kind in ("logical", "semantic") else "logical",
                })

    if language in ("python", "py"):
        static_issues = _python_logical_analysis_issues(code)
        existing_messages = {issue["message"] for issue in issues}
        for issue in static_issues:
            if issue["message"] not in existing_messages:
                issues.insert(0, issue)

    if issues:
        first_issue = issues[0]
        issue_msg = first_issue.get("message", "")
        if issue_msg and not any(w in narration.lower() for w in ("error", "mistake", "issue", "bug", "wrong", "incorrect")):
            line_no = first_issue.get("line")
            loc_str = f"on line {line_no}" if line_no else "in your code"
            if narration:
                narration = f"Note: There is a logical error {loc_str}. {issue_msg} " + narration
            else:
                narration = f"Found a logical error {loc_str}: {issue_msg}"

    return {"steps": steps, "narration": narration, "issues": issues}


def llm_check_semantic_errors(code: str, language: str = "python") -> list[dict]:
    """Fast, lightweight semantic and logical error check without full code narration."""
    language = (language or "python").lower()

    # 1. Instant static analysis (<1ms)
    if language in ("python", "py"):
        static_issues = _python_logical_analysis_issues(code)
        if static_issues:
            return static_issues

    # 2. Fast LLM check capped at 160 tokens
    code_snippet = (code or "")[:4000]
    messages = [
        {"role": "system", "content": SEMANTIC_CHECK_SYSTEM_PROMPT},
        {"role": "user", "content": f"Language: {language}\n\nCode:\n{code_snippet}"},
    ]

    try:
        result = _chat_completion(
            messages=messages,
            temperature=0.1,
            max_tokens=160,
        )
        raw = result["choices"][0]["message"]["content"]
    except Exception:
        return []

    data = _to_json(raw)
    raw_issues = data.get("issues") if isinstance(data, dict) else []
    issues = []
    if isinstance(raw_issues, list):
        for issue in raw_issues:
            if not isinstance(issue, dict):
                continue
            try:
                line = int(issue.get("line", 1))
            except (TypeError, ValueError):
                line = 1
            message = issue.get("message")
            kind = issue.get("kind")
            if isinstance(message, str) and message.strip():
                issues.append({
                    "line": max(1, line),
                    "message": message.strip(),
                    "kind": kind if kind in ("logical", "semantic") else "logical",
                })

    return issues

def llm_explain_symbol(code: str, language: str, symbol: str, kind: str = "", seed: int = 42) -> dict:
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
        result = _chat_completion(
            messages=messages,
            temperature=0.1,
            max_tokens=640,
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


def _fix_common_syntax_typo(
    code: str,
    err_line: Optional[int],
    error_message: str = "",
) -> tuple[str, bool]:
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

    if "unterminated string" in error_message.lower():
        for idx in target_indices:
            line = lines[idx]
            quote: Optional[str] = None
            escaped = False
            for character in line:
                if escaped:
                    escaped = False
                    continue
                if character == "\\":
                    escaped = True
                    continue
                if quote is None and character in ("'", '"'):
                    quote = character
                elif quote == character:
                    quote = None

            if quote is None:
                continue

            closing_index = len(line)
            while closing_index > 0 and line[closing_index - 1].isspace():
                closing_index -= 1
            if closing_index > 0 and line[closing_index - 1] in ")]}":
                lines[idx] = (
                    line[: closing_index - 1]
                    + quote
                    + line[closing_index - 1 :]
                )
            else:
                lines[idx] = line + quote
            return "\n".join(lines), True

    return code, False


def llm_fix_python_error(*, code: str, error: str, temperature: float = 0.1, num_predict: int = 1000) -> dict:
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
            result = _chat_completion(
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
            new_code, ok = _fix_common_syntax_typo(
                current_code,
                err_line,
                error_message=current_error,
            )
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


def _python_logical_analysis_issues(code: str) -> list[dict]:
    """Find a comprehensive set of unambiguous logical/semantic mistakes without relying on the LLM."""
    import ast

    try:
        tree = ast.parse(code or "")
    except SyntaxError:
        return []

    issues: list[dict] = []

    # 1. Discount / deduction added to subtotal, total, price, or cost
    DISCOUNT_WORDS = ("discount", "deduction", "coupon", "rebate", "markdown", "saving", "promo", "voucher")
    TOTAL_WORDS = ("subtotal", "total", "price", "cost", "amount", "bill", "pay", "charge", "due", "fee")

    for node in ast.walk(tree):
        if isinstance(node, (ast.Return, ast.Assign, ast.AugAssign)):
            val = node.value
            target_names = set()
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        target_names.add(t.id.lower())
            elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
                target_names.add(node.target.id.lower())

            if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add):
                val_names = {c.id.lower() for c in ast.walk(val) if isinstance(c, ast.Name)}
                has_discount = any(any(dw in n for dw in DISCOUNT_WORDS) for n in val_names | target_names)
                if has_discount:
                    issues.append({
                        "line": node.lineno,
                        "message": (
                            "The discount is added to the total, which increases the price instead of reducing it. "
                            "A discount should normally be subtracted."
                        ),
                        "kind": "logical",
                    })
            elif val and isinstance(val, ast.BinOp) and isinstance(val.op, ast.Add):
                val_names = {c.id.lower() for c in ast.walk(val) if isinstance(c, ast.Name)}
                all_names = val_names | target_names
                has_discount = any(any(dw in n for dw in DISCOUNT_WORDS) for n in all_names)
                if has_discount:
                    issues.append({
                        "line": node.lineno,
                        "message": (
                            "The discount is added to the amount, which increases the total instead of reducing it. "
                            "A discount should normally be subtracted."
                        ),
                        "kind": "logical",
                    })

    # 1b. Tax, tip, fee, surcharge, shipping subtracted from subtotal, total, price, or cost
    SURCHARGE_WORDS = ("tax", "tip", "fee", "surcharge", "shipping", "delivery", "interest", "markup")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Return, ast.Assign, ast.AugAssign)):
            val = node.value
            target_names = set()
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        target_names.add(t.id.lower())
            elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
                target_names.add(node.target.id.lower())

            if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Sub):
                val_names = {c.id.lower() for c in ast.walk(val) if isinstance(c, ast.Name)}
                has_surcharge = any(any(sw in n for sw in SURCHARGE_WORDS) for n in val_names | target_names)
                if has_surcharge:
                    issues.append({
                        "line": node.lineno,
                        "message": (
                            "The tax, tip, or fee is subtracted from the total, reducing the cost instead of adding to it. "
                            "Taxes and fees should normally be added."
                        ),
                        "kind": "logical",
                    })
            elif val and isinstance(val, ast.BinOp) and isinstance(val.op, ast.Sub):
                right_names = {c.id.lower() for c in ast.walk(val.right) if isinstance(c, ast.Name)}
                if any(any(sw in n for sw in SURCHARGE_WORDS) for n in right_names):
                    issues.append({
                        "line": node.lineno,
                        "message": (
                            "The tax, tip, or fee is subtracted from the amount instead of added. "
                            "Taxes, tips, and fees should normally be added to the total."
                        ),
                        "kind": "logical",
                    })

    # 2. Average / mean calculation mistakes
    for node in ast.walk(tree):
        # Operator precedence bug in average: e.g. a + b / 2
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            div_node = None
            if isinstance(node.right, ast.BinOp) and isinstance(node.right.op, ast.Div):
                div_node = node.right
            elif isinstance(node.left, ast.BinOp) and isinstance(node.left.op, ast.Div):
                div_node = node.left
            if div_node:
                denom = div_node.right
                if isinstance(denom, ast.Constant) and isinstance(denom.value, (int, float)) and denom.value >= 2:
                    issues.append({
                        "line": node.lineno,
                        "message": (
                            "Due to operator precedence, division is calculated before addition. "
                            "Wrap the addition in parentheses before dividing, such as (a + b) / 2."
                        ),
                        "kind": "logical",
                    })

    # Average divisor mismatch (e.g. (a + b + c) / 2) across both functions and top-level code
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            numerator = node.left
            denominator = node.right
            if isinstance(denominator, ast.Constant) and isinstance(denominator.value, (int, float)):
                terms = 1
                for item in ast.walk(numerator):
                    if isinstance(item, ast.BinOp) and isinstance(item.op, ast.Add):
                        terms += 1
                if terms > 1 and denominator.value != terms:
                    val_str = str(int(denominator.value)) if isinstance(denominator.value, int) or getattr(denominator.value, "is_integer", lambda: False)() else str(denominator.value)
                    issues.append({
                        "line": node.lineno,
                        "message": (
                            f"The calculation adds {terms} values but divides by {val_str}; "
                            f"an average should divide by {terms}."
                        ),
                        "kind": "semantic",
                    })

    # 3. Product accumulator initialized to 0
    for func in ast.walk(tree):
        if isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
            zero_accumulators = {}
            for stmt in getattr(func, "body", []):
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            name_lower = target.id.lower()
                            if any(w in name_lower for w in ("prod", "product", "mult", "factorial")):
                                if isinstance(stmt.value, ast.Constant) and stmt.value.value == 0:
                                    zero_accumulators[target.id] = stmt.lineno
                elif isinstance(stmt, (ast.For, ast.While)):
                    for sub in ast.walk(stmt):
                        var_id = None
                        is_mult = False
                        if isinstance(sub, ast.AugAssign) and isinstance(sub.op, ast.Mult) and isinstance(sub.target, ast.Name):
                            var_id = sub.target.id
                            is_mult = True
                        elif isinstance(sub, ast.Assign) and len(sub.targets) == 1 and isinstance(sub.targets[0], ast.Name):
                            target_id = sub.targets[0].id
                            if isinstance(sub.value, ast.BinOp) and isinstance(sub.value.op, ast.Mult):
                                if any(isinstance(c, ast.Name) and c.id == target_id for c in ast.walk(sub.value)):
                                    var_id = target_id
                                    is_mult = True
                        if is_mult and var_id in zero_accumulators:
                            line = zero_accumulators[var_id]
                            issues.append({
                                "line": line,
                                "message": (
                                    f"The accumulator '{var_id}' is initialized to 0 and then multiplied, "
                                    "which will always produce 0. Initialize it to 1 instead."
                                ),
                                "kind": "logical",
                            })
                            del zero_accumulators[var_id]

    # 4. Accumulator reset inside loop
    for loop in ast.walk(tree):
        if isinstance(loop, (ast.For, ast.While)):
            body = loop.body
            for i, stmt in enumerate(body):
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                    t_name = stmt.targets[0].id
                    if any(w in t_name.lower() for w in ("total", "sum", "count", "accum", "tally")):
                        if isinstance(stmt.value, ast.Constant) and stmt.value.value in (0, 0.0):
                            for rest in body[i + 1:]:
                                for sub in ast.walk(rest):
                                    if isinstance(sub, ast.AugAssign) and isinstance(sub.target, ast.Name) and sub.target.id == t_name:
                                        issues.append({
                                            "line": stmt.lineno,
                                            "message": (
                                                f"'{t_name}' is reset to 0 inside the loop on each iteration. "
                                                "It should be initialized outside the loop before iterating."
                                            ),
                                            "kind": "logical",
                                        })
                                        break

    # 5. Contradictory conditions: x > A and x < B where A >= B
    for node in ast.walk(tree):
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
            comps = [v for v in node.values if isinstance(v, ast.Compare)]
            for i in range(len(comps)):
                for j in range(i + 1, len(comps)):
                    c1, c2 = comps[i], comps[j]
                    if len(c1.ops) == 1 and len(c2.ops) == 1 and len(c1.comparators) == 1 and len(c2.comparators) == 1:
                        if isinstance(c1.left, ast.Name) and isinstance(c2.left, ast.Name) and c1.left.id == c2.left.id:
                            op1, op2 = type(c1.ops[0]), type(c2.ops[0])
                            v1, v2 = c1.comparators[0], c2.comparators[0]
                            if isinstance(v1, ast.Constant) and isinstance(v2, ast.Constant) and isinstance(v1.value, (int, float)) and isinstance(v2.value, (int, float)):
                                if (op1 is ast.Gt and op2 is ast.Lt and v1.value >= v2.value) or (op1 is ast.Lt and op2 is ast.Gt and v2.value >= v1.value):
                                    issues.append({
                                        "line": node.lineno,
                                        "message": f"The condition on '{c1.left.id}' is contradictory and can never be true.",
                                        "kind": "logical",
                                    })

    # 5b. Always-true disjunction with != on distinct constants: e.g. x != 'a' or x != 'b'
    for node in ast.walk(tree):
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            comps = [v for v in node.values if isinstance(v, ast.Compare)]
            for i in range(len(comps)):
                for j in range(i + 1, len(comps)):
                    c1, c2 = comps[i], comps[j]
                    if len(c1.ops) == 1 and isinstance(c1.ops[0], ast.NotEq) and len(c2.ops) == 1 and isinstance(c2.ops[0], ast.NotEq):
                        if isinstance(c1.left, ast.Name) and isinstance(c2.left, ast.Name) and c1.left.id == c2.left.id:
                            v1 = c1.comparators[0] if c1.comparators else None
                            v2 = c2.comparators[0] if c2.comparators else None
                            if isinstance(v1, ast.Constant) and isinstance(v2, ast.Constant) and v1.value != v2.value:
                                issues.append({
                                    "line": node.lineno,
                                    "message": (
                                        f"The condition '{c1.left.id} != {repr(v1.value)} or {c2.left.id} != {repr(v2.value)}' "
                                        "is always True because a variable cannot equal two different values at once. Use 'and' instead of 'or'."
                                    ),
                                    "kind": "logical",
                                })

    # 6. Truthy constant in boolean OR (e.g. if x == 1 or 2: or if s == 'y' or 'yes':)
    for node in ast.walk(tree):
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            for val in node.values[1:]:
                if isinstance(val, ast.Constant) and bool(val.value):
                    issues.append({
                        "line": node.lineno,
                        "message": (
                            f"The 'or' condition includes a constant '{val.value}' which is always truthy. "
                            f"This makes the entire condition evaluate to True every time. "
                            f"Write each comparison explicitly, such as variable == {repr(val.value)}."
                        ),
                        "kind": "logical",
                    })
                    break

    # 7. Unconditional return at start of loop
    for loop in ast.walk(tree):
        if isinstance(loop, (ast.For, ast.While)):
            if loop.body and isinstance(loop.body[0], ast.Return):
                issues.append({
                    "line": loop.body[0].lineno,
                    "message": (
                        "The return statement is placed unconditionally inside the loop. "
                        "This causes the loop to exit on the very first iteration."
                    ),
                    "kind": "logical",
                })

    # 8. Variable swap overwritten before reading (e.g. a = b; b = a)
    for parent in ast.walk(tree):
        body = getattr(parent, "body", None)
        if isinstance(body, list) and len(body) >= 2:
            for i in range(len(body) - 1):
                s1, s2 = body[i], body[i + 1]
                if (isinstance(s1, ast.Assign) and len(s1.targets) == 1 and isinstance(s1.targets[0], ast.Name)
                    and isinstance(s1.value, ast.Name)):
                    if (isinstance(s2, ast.Assign) and len(s2.targets) == 1 and isinstance(s2.targets[0], ast.Name)
                        and isinstance(s2.value, ast.Name)):
                        if s1.targets[0].id == s2.value.id and s1.value.id == s2.targets[0].id:
                            issues.append({
                                "line": s2.lineno,
                                "message": (
                                    f"Attempted to swap '{s1.targets[0].id}' and '{s1.value.id}', but '{s1.targets[0].id}' "
                                    f"was already overwritten on the previous line. Use tuple unpacking 'a, b = b, a' instead."
                                ),
                                "kind": "logical",
                            })

    # 9. Inverted min/max logic:
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Compare) and len(test.ops) == 1 and len(test.comparators) == 1:
                op = test.ops[0]
                left = test.left
                right = test.comparators[0]
                if isinstance(left, ast.Name) and isinstance(right, ast.Name):
                    left_lower = left.id.lower()
                    right_lower = right.id.lower()
                    # finding max: if val < max_val: max_val = val
                    if any(w in right_lower for w in ("max", "largest", "highest")) and isinstance(op, (ast.Lt, ast.LtE)):
                        for s in node.body:
                            if isinstance(s, ast.Assign) and any(isinstance(t, ast.Name) and t.id == right.id for t in s.targets):
                                issues.append({
                                    "line": node.lineno,
                                    "message": (
                                        f"When tracking the maximum value '{right.id}', the condition checks if '{left.id} < {right.id}'. "
                                        "This inverts the maximum logic; it should check if the new value is greater than the current maximum."
                                    ),
                                    "kind": "logical",
                                })
                                break
                    # finding min: if val > min_val: min_val = val
                    elif any(w in right_lower for w in ("min", "smallest", "lowest")) and isinstance(op, (ast.Gt, ast.GtE)):
                        for s in node.body:
                            if isinstance(s, ast.Assign) and any(isinstance(t, ast.Name) and t.id == right.id for t in s.targets):
                                issues.append({
                                    "line": node.lineno,
                                    "message": (
                                        f"When tracking the minimum value '{right.id}', the condition checks if '{left.id} > {right.id}'. "
                                        "This inverts the minimum logic; it should check if the new value is less than the current minimum."
                                    ),
                                    "kind": "logical",
                                })
                                break

    # 10. Function formula bugs: area adding, perimeter multiplying, inverted even/odd
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fname = node.name.lower()
            if "area" in fname and not any(w in fname for w in ("surface", "trapezoid", "triangle")):
                for ret in ast.walk(node):
                    if isinstance(ret, ast.Return) and isinstance(ret.value, ast.BinOp) and isinstance(ret.value.op, ast.Add):
                        issues.append({
                            "line": ret.lineno,
                            "message": (
                                f"The function '{node.name}' adds dimensions instead of multiplying them. "
                                "Calculating area typically requires multiplying dimensions."
                            ),
                            "kind": "semantic",
                        })
            elif "perimeter" in fname:
                for ret in ast.walk(node):
                    if isinstance(ret, ast.Return) and isinstance(ret.value, ast.BinOp) and isinstance(ret.value.op, ast.Mult):
                        issues.append({
                            "line": ret.lineno,
                            "message": (
                                f"The function '{node.name}' multiplies dimensions instead of adding them. "
                                "Calculating perimeter requires adding the sides."
                            ),
                            "kind": "semantic",
                        })
            elif "even" in fname:
                for ret in ast.walk(node):
                    if isinstance(ret, ast.Return) and isinstance(ret.value, ast.Compare):
                        cmp = ret.value
                        if len(cmp.ops) == 1 and isinstance(cmp.ops[0], ast.Eq) and len(cmp.comparators) == 1:
                            if isinstance(cmp.left, ast.BinOp) and isinstance(cmp.left.op, ast.Mod):
                                if isinstance(cmp.left.right, ast.Constant) and cmp.left.right.value == 2:
                                    if isinstance(cmp.comparators[0], ast.Constant) and cmp.comparators[0].value == 1:
                                        issues.append({
                                            "line": ret.lineno,
                                            "message": f"The function '{node.name}' checks if the number modulo 2 equals 1, which identifies odd numbers, not even numbers.",
                                            "kind": "logical",
                                        })
            elif "odd" in fname:
                for ret in ast.walk(node):
                    if isinstance(ret, ast.Return) and isinstance(ret.value, ast.Compare):
                        cmp = ret.value
                        if len(cmp.ops) == 1 and isinstance(cmp.ops[0], ast.Eq) and len(cmp.comparators) == 1:
                            if isinstance(cmp.left, ast.BinOp) and isinstance(cmp.left.op, ast.Mod):
                                if isinstance(cmp.left.right, ast.Constant) and cmp.left.right.value == 2:
                                    if isinstance(cmp.comparators[0], ast.Constant) and cmp.comparators[0].value == 0:
                                        issues.append({
                                            "line": ret.lineno,
                                            "message": f"The function '{node.name}' checks if the number modulo 2 equals 0, which identifies even numbers, not odd numbers.",
                                            "kind": "logical",
                                        })

    # 11. Identity check on literal: 'x is 5' or 'x is "hello"'
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for op, comp in zip(node.ops, node.comparators):
                if isinstance(op, (ast.Is, ast.IsNot)) and isinstance(comp, ast.Constant) and comp.value is not None:
                    word = "is" if isinstance(op, ast.Is) else "is not"
                    issues.append({
                        "line": node.lineno,
                        "message": (
                            f"The code uses '{word}' to compare with literal {repr(comp.value)}. "
                            "In Python, 'is' checks object identity, not equality. Use '==' or '!=' instead."
                        ),
                        "kind": "logical",
                    })

    # 12. Off-by-one in range loops: for i in range(len(lst) + 1): ... lst[i]
    for loop in ast.walk(tree):
        if isinstance(loop, ast.For) and isinstance(loop.target, ast.Name):
            iter_node = loop.iter
            if isinstance(iter_node, ast.Call) and isinstance(iter_node.func, ast.Name) and iter_node.func.id == "range":
                if iter_node.args:
                    arg = iter_node.args[-1]
                    if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add) and isinstance(arg.right, ast.Constant) and arg.right.value == 1:
                        if isinstance(arg.left, ast.Call) and isinstance(arg.left.func, ast.Name) and arg.left.func.id == "len":
                            issues.append({
                                "line": loop.lineno,
                                "message": (
                                    "The range bound is set to len(...) + 1. "
                                    "Because Python uses 0-based indexing up to len - 1, accessing elements by this index will raise an IndexError."
                                ),
                                "kind": "semantic",
                            })

    # Deduplicate issues by line and message
    seen = set()
    unique_issues = []
    for issue in issues:
        key = (issue.get("line"), issue.get("message"))
        if key not in seen:
            seen.add(key)
            unique_issues.append(issue)

    return unique_issues

def chat(message: str) -> dict:
    _ensure_qa_loaded()
    msg = (message or "").strip()
    if not msg:
        return {"reply": unclear_response(), "question_id": None}

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

    return {"reply": unclear_response(), "question_id": None}

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

def llm_code_review(code: str, language: str, *, temperature: float = 0.1, num_predict: int = 1500, seed: int = 42) -> dict:
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
        result = _chat_completion(
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