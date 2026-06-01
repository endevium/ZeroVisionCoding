from __future__ import annotations

import re
from typing import Optional

def extract_after_phrase(text: str, phrases: list[str]) -> str:
    text = (text or "").strip().lower()
    for phrase in phrases:
        idx = text.find(phrase)
        if idx != -1:
            return text[idx + len(phrase):].strip()
    return ""

def normalize_spoken_filename(spoken: str) -> str:
    spoken = (spoken or "").strip().lower().replace('"', "").replace("'", "")
    tokens = [t for t in spoken.replace("/", " ").replace("\\", " ").split() if t]

    parts: list[str] = []
    for tok in tokens:
        if tok in ("dot", "period", "point"):
            parts.append(".")
            continue
        if tok in ("dash", "hyphen"):
            parts.append("-")
            continue
        if tok in ("underscore", "under", "under-score"):
            parts.append("_")
            continue

        cleaned = "".join(ch for ch in tok if ch.isalnum())
        if cleaned:
            parts.append(cleaned)

    name = "".join(parts)
    if name and "." not in name:
        name += ".py"
    return name

def _safe_slice_lines(lines: list[str], start: int, end: int) -> str:
    start = max(0, start)
    end = min(len(lines), end)
    return "\n".join(lines[start:end]).strip()

def extract_snippet_around(text: str, needle: str, *, max_lines: int = 80) -> str:
    """Generic fallback: grab a window of lines around first occurrence of needle."""
    text = text or ""
    needle = (needle or "").strip()
    if not text:
        return ""
    lines = text.splitlines()
    if not needle:
        return _safe_slice_lines(lines, 0, min(len(lines), max_lines))

    hit = None
    for i, line in enumerate(lines):
        if needle in line:
            hit = i
            break
    if hit is None:
        # head+tail
        half = max_lines // 2
        head = _safe_slice_lines(lines, 0, half)
        tail = _safe_slice_lines(lines, max(0, len(lines) - half), len(lines))
        if tail and head and head != tail:
            return (head + "\n\n... truncated ...\n\n" + tail).strip()
        return head or tail

    half = max_lines // 2
    return _safe_slice_lines(lines, hit - half, hit + half)

def extract_python_symbol_block(code: str, symbol: str, *, kind: str = "") -> Optional[str]:
    """
    Best-effort Python: find the def/class block for `symbol` using AST.
    Returns a code snippet (few dozen lines) or None.
    """
    code = code or ""
    symbol = (symbol or "").strip()
    if not code or not symbol:
        return None

    try:
        import ast
        tree = ast.parse(code)
    except Exception:
        return None

    # Find a matching node
    target = None
    for node in ast.walk(tree):
        if kind == "function" and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol:
            target = node
            break
        if kind == "class" and isinstance(node, ast.ClassDef) and node.name == symbol:
            target = node
            break
        if not kind and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and getattr(node, "name", None) == symbol:
            target = node
            break

    if not target or not hasattr(target, "lineno"):
        return None

    lines = code.splitlines()
    start = max(0, int(getattr(target, "lineno", 1)) - 1)
    end = int(getattr(target, "end_lineno", start + 1) or (start + 1))

    # Expand slightly to include decorators and a bit of context
    start = max(0, start - 3)
    end = min(len(lines), end + 8)

    return "\n".join(lines[start:end]).strip()