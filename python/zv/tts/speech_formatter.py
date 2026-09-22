from __future__ import annotations

import re
from typing import Dict


# Keep this table deliberately small and easy to extend. Values are spoken
# forms, not replacements that remove technical meaning.
TECHNICAL_TERMS: Dict[str, str] = {
    "API": "A P I",
    "TTS": "T T S",
    "LLM": "L L M",
    "RAG": "R A G",
    "VSCode": "V S Code",
    "FastAPI": "Fast A P I",
    "KPipeline": "K Pipeline",
    "Qwen2.5": "Qwen two point five",
}

_TERM_PATTERN = re.compile(
    "|".join(sorted((re.escape(key) for key in TECHNICAL_TERMS), key=len, reverse=True)),
    re.IGNORECASE,
)
_WINDOWS_PATH_PATTERN = re.compile(r"(?<![\w])(?:[A-Za-z]:[\\/])(?:[^ \t\r\n,;]+)")
_UNIX_PATH_PATTERN = re.compile(r"(?<![\w])/(?:[^ \t\r\n,;]+/)*[^ \t\r\n,;]+")
_FILENAME_PATTERN = re.compile(r"(?<![\w/\\])([A-Za-z0-9][A-Za-z0-9_-]*)\.(py|json|js|ts|tsx|jsx|yaml|yml|toml|md|txt|ini|cfg|cpp|c|h)(?![\w])", re.IGNORECASE)

_CODE_OPERATORS = (
    ("==", "is equal to"),
    ("!=", "is not equal to"),
    (">=", "is greater than or equal to"),
    ("<=", "is less than or equal to"),
    ("=>", "arrow"),
    ("->", "arrow"),
    ("+=", "plus equals"),
    ("-=", "minus equals"),
    ("*=", "asterisk equals"),
    ("/=", "slash equals"),
    ("++", "plus plus"),
    ("--", "minus minus"),
    ("&&", "and"),
    ("||", "or"),
    ("+", "plus"),
    ("-", "minus"),
    ("*", "asterisk"),
    ("/", "slash"),
    ("%", "percent"),
    ("=", "equals"),
    (">", "greater than"),
    ("<", "less than"),
    ("(", "opening parenthesis"),
    (")", "closing parenthesis"),
    ("[", "opening bracket"),
    ("]", "closing bracket"),
    ("{", "opening brace"),
    ("}", "closing brace"),
    (":", "colon"),
    (";", "semicolon"),
    ("#", "hash"),
    ("_", "underscore"),
)
_CODE_OPERATOR_PATTERN = re.compile(
    "|".join(re.escape(operator) for operator, _ in _CODE_OPERATORS)
)
_CODE_OPERATOR_WORDS = dict(_CODE_OPERATORS)
_QUOTED_TEXT_PATTERN = re.compile(r"""('(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")""")


def _replace_terms(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        original = match.group(0)
        for name, spoken in TECHNICAL_TERMS.items():
            if original.lower() == name.lower():
                return spoken
        return original

    return _TERM_PATTERN.sub(replace, text)


def _words_for_identifier(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    return value.replace("_", " underscore ").strip()


def _spoken_filename(match: re.Match[str]) -> str:
    stem = _words_for_identifier(match.group(1).replace("-", " minus "))
    extension = match.group(2).lower()
    extension_names = {
        "py": "Python file",
        "json": "JSON file",
        "js": "JavaScript file",
        "ts": "TypeScript file",
        "tsx": "TSX file",
        "jsx": "JSX file",
        "yaml": "YAML file",
        "yml": "YAML file",
        "toml": "TOML file",
        "md": "Markdown file",
        "txt": "text file",
        "ini": "INI file",
        "cfg": "configuration file",
        "cpp": "C plus plus file",
        "c": "C file",
        "h": "header file",
    }
    return f"{stem} {extension_names[extension]}"


def _spoken_path(value: str) -> str:
    drive = ""
    remainder = value
    drive_match = re.match(r"([A-Za-z]):[\\/]", value)
    if drive_match:
        drive = f"{drive_match.group(1).upper()} drive, "
        remainder = value[3:]

    parts = [part for part in re.split(r"[\\/]+", remainder) if part]
    spoken_parts = []
    for part in parts:
        filename = _FILENAME_PATTERN.fullmatch(part)
        spoken_parts.append(_spoken_filename(filename) if filename else _words_for_identifier(part))
    return drive + ", ".join(spoken_parts)


def _format_paths_and_filenames(text: str) -> str:
    text = _WINDOWS_PATH_PATTERN.sub(lambda match: _spoken_path(match.group(0)), text)
    text = _UNIX_PATH_PATTERN.sub(lambda match: _spoken_path(match.group(0)), text)
    return _FILENAME_PATTERN.sub(_spoken_filename, text)


def format_explanation(text: str) -> str:
    """Make technical names and file references speakable without code syntax rewriting."""
    value = (text or "").strip()
    if not value:
        return ""
    return _format_paths_and_filenames(_replace_terms(value)).strip()


def _format_code_segment(segment: str) -> str:
    segment = _format_paths_and_filenames(_replace_terms(segment))
    segment = _CODE_OPERATOR_PATTERN.sub(
        lambda match: f" {_CODE_OPERATOR_WORDS[match.group(0)]} ",
        segment,
    )
    segment = re.sub(r"\s+", " ", segment)
    return segment.strip()


def format_code(text: str) -> str:
    """Convert code syntax to spoken descriptions while preserving quoted content."""
    value = (text or "").strip()
    if not value:
        return ""

    pieces = []
    last_end = 0
    for match in _QUOTED_TEXT_PATTERN.finditer(value):
        pieces.append(_format_code_segment(value[last_end:match.start()]))
        quoted = format_explanation(match.group(0)[1:-1])
        pieces.append(f" {quoted} ")
        last_end = match.end()
    pieces.append(_format_code_segment(value[last_end:]))

    spoken = " ".join(piece for piece in pieces if piece.strip())
    spoken = re.sub(r"\s*,\s*", ", ", spoken)
    spoken = re.sub(r"\s*\n+\s*", ", ", spoken)
    return re.sub(r"\s+", " ", spoken).strip(" ,")

