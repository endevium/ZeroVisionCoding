from __future__ import annotations
import json
import requests
from pathlib import Path

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
    "You are a code assistant.\n"
    "You will be given a Python file and a traceback/error message.\n"
    "Fix the error with the smallest reasonable change.\n"
    "Do NOT change unrelated formatting.\n"
    "Return ONLY valid JSON with this exact schema:\n"
    "{\n"
    '  "content": string,\n'
    '  "summary": string\n'
    "}\n"
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

def ollama_chat(user_message: str, *, temperature: float = 0.3, num_predict: int = 120) -> dict:
    qa_ctx = _build_qa_context(user_message, k=3)
    combined_message = f"{user_message}\n\n{qa_ctx}" if qa_ctx else user_message

    payload = {
        "model": MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": combined_message},
        ],
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
        },
    }

    try:
        r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
        raw = r.json()["message"]["content"]
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

def ollama_analyze(code: str, language: str, *, temperature: float = 0.2, num_predict: int = 1000) -> dict:
    language = (language or "python").lower()
    if language in ("python", "py"):
        outline = _python_outline(code)
        snippet = (code or "")[:4000]
        code_for_llm = f"OUTLINE:\n{outline}\n\nSNIPPET:\n{snippet}"
    else:
        code_for_llm = (code or "")[:8000]
    
    payload = {
        "model": MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": ANALYZE_SYSTEM_PROMPT},
            {"role": "user", "content": f"Language: {language}\n\nCode:\n{code_for_llm}"},
        ],
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
        },
    }

    try:
        r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=60)
        r.raise_for_status()
        raw = r.json()["message"]["content"]
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

def ollama_explain_symbol(code: str, language: str, symbol: str, kind: str = "") -> dict:
    payload = {
        "model": MODEL,
        "stream": False,
        "messages": [
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
        ],
        "options": {"temperature": 0.2, "num_predict": 160},
    }

    try:
        r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
        raw = r.json()["message"]["content"]
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

def ollama_fix_python_error(*, code: str, error: str, temperature: float = 0.0, num_predict: int = 600) -> dict:
    payload = {
        "model": MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": FIX_PYTHON_ERROR_PROMPT},
            {
                "role": "user",
                "content": (
                    "Python file content:\n"
                    f"{code}\n\n"
                    "Traceback / error:\n"
                    f"{error}\n"
                ),
            },
        ],
        "options": {"temperature": temperature, "num_predict": num_predict},
    }

    try:
        r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
        raw = r.json()["message"]["content"]
    except Exception:
        return {"content": "", "summary": "Fix failed. The local LLM service returned an error."}

    data = _to_json(raw)
    content = data.get("content")
    summary = data.get("summary")

    if not isinstance(content, str) or not content.strip():
        return {"content": "", "summary": _strip_code_fences(raw).strip() or "Fix failed."}

    if not isinstance(summary, str):
        summary = "Applied a fix."

    return {"content": content, "summary": summary}

def _strip_code_fences(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("```"):
        lines = s.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        s = "\n".join(lines).strip()
    return s

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