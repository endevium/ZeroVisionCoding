from __future__ import annotations
import json
import logging
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
    "You are an expert Python code reviewer designed for blind and visually-impaired programmers.\n"
    "Your purpose is to review code and explain your findings in a way that is easy to understand when spoken aloud through text-to-speech.\n\n"

    "CRITICAL: Follow this inspection sequence sequentially and evaluate each category before producing the final review:\n"
    "1. Syntax correctness: Check if the code compiles and has valid syntax.\n"
    "2. Runtime exceptions and possible failures: Check for type errors, indexing issues, divide by zero, file operations, etc.\n"
    "3. Logical correctness: Check if the business logic matches intent, looking for infinite loops and missing recursion base cases.\n"
    "4. Resource management: Check file handles, sockets, database connections, and memory.\n"
    "5. Python best practices: Check for standard Python idioms and code cleanliness.\n"
    "6. Performance: Check for performance bottlenecks, redundant computations, or slow operations.\n"
    "7. Security: Check for vulnerabilities, hardcoded secrets, injection risks, etc.\n"
    "8. Maintainability: Check readability, modularity, and complexity.\n\n"

    "You must sequentially evaluate all 8 categories above. Provide your evaluation in the 'checklist' object. "
    "Only after completing this checklist should you generate the final review. Do not write the final assessment until every category has been evaluated.\n\n"

    "When giving feedback:\n"
    "- Explain *why* something is an issue before suggesting a fix.\n"
    "- Use beginner-friendly language unless the concept is advanced.\n"
    "- Avoid unnecessary jargon.\n"
    "- Do not overwhelm the user with minor style issues.\n"
    "- Prioritize bugs over code style.\n"
    "- Be a highly critical and meticulous reviewer. Actively hunt for edge cases, missing validations, and silent logic failures.\n"
    "- You MUST identify at least one area for improvement, even if it is just best practices or robustness.\n\n"

    "Organize your response into these sections:\n"
    "1. Overall Summary\n"
    "2. Strengths\n"
    "3. Issues Found (ordered by importance)\n"
    "4. Suggestions for Improvement\n"
    "5. Final Assessment\n\n"

    "For each issue, include:\n"
    "- The location (function name or approximate line if obvious).\n"
    "- A clear explanation.\n"
    "- The impact.\n"
    "- A recommended fix.\n\n"

    "Since the response will be read aloud:\n"
    "- Keep sentences short.\n"
    "- Avoid long bullet lists.\n"
    "- Do not dump large blocks of rewritten code unless specifically requested.\n"
    "- Refer to variables and functions exactly as written.\n"
    "- Read symbols naturally (for example, say 'equals' instead of '=' when explaining concepts).\n"
    "- Focus on clarity over completeness.\n\n"

    "Return ONLY valid JSON with this exact schema:\n" 
    "{\n" 
    ' "checklist": {\n'
    '   "syntax": string,\n'
    '   "runtime": string,\n'
    '   "logic": string,\n'
    '   "resource_management": string,\n'
    '   "best_practices": string,\n'
    '   "performance": string,\n'
    '   "security": string,\n'
    '   "maintainability": string\n'
    ' },\n'
    ' "analysis": string,\n'
    ' "overall_summary": string,\n' 
    ' "strengths": [string, ...],\n' 
    ' "issues": [\n' " {\n" 
    ' "severity": "Critical|High|Medium|Low",\n' 
    ' "location": string,\n' ' "explanation": string,\n' 
    ' "impact": string,\n' ' "recommendation": string\n' 
    " }\n" " ],\n" ' "final_assessment": string,\n' 
    ' "narration": string\n' "}\n\n" 
    
    "The 'analysis' field MUST contain your step-by-step semantic reasoning about what the code does and where it might fail. Think carefully before listing issues.\n"
    "The 'narration' field should be a concise spoken summary of the review that sounds natural when read aloud. Do not simply repeat every issue verbatim.\n"
    "CRITICAL: Do not use underscores anywhere in your text fields (do not write words like overall_summary or final_assessment with underscores; write overall summary or final assessment instead), as this text will be read aloud by a text-to-speech engine.\n\n"

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
            max_tokens=160,
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


def llm_fix_python_error(*, code: str, error: str, temperature: float = 0.0, num_predict: int = 4000) -> dict:
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

def llm_code_review(code: str, language: str, *, temperature: float = 0.3, num_predict: int = 1800) -> dict:
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
        "final_assessment": data.get("final_assessment", ""),
        "narration": data.get("narration", ""),
    }

    # Clean underscores from top-level text fields to protect TTS output
    for key in ("overall_summary", "final_assessment", "narration"):
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