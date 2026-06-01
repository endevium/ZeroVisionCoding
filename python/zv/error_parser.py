from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ParsedPythonError:
    file: str
    line: int
    column: Optional[int]
    message: str
    raw: str

_TB_RE = re.compile(r'File "([^"]+)", line (\d+)')
_CARET_LINE_RE = re.compile(r"^(?P<indent>\s*)\^\s*$")

def parse_python_traceback(stderr_text: str) -> Optional[ParsedPythonError]:
    s = (stderr_text or "").strip()
    if not s:
        return None

    lines = s.splitlines()

    last_match = None
    for i, line in enumerate(lines):
        m = _TB_RE.search(line)
        if m:
            last_match = (i, m.group(1), int(m.group(2)))

    if not last_match:
        return None

    _, file, line_no = last_match

    col: Optional[int] = None
    for line in lines:
        m = _CARET_LINE_RE.match(line)
        if m:
            col = len(m.group("indent")) + 1
            break

    msg = ""
    for l in reversed(lines):
        t = l.strip()
        if t:
            msg = t
            break

    return ParsedPythonError(file=file, line=line_no, column=col, message=msg, raw=s)