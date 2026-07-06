from __future__ import annotations
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    
class ChatResponse(BaseModel):
    reply: str
    
class AnalyzeFromEditorRequest(BaseModel):
    useActiveEditor: bool = True

class AnalyzeRequest(BaseModel):
    code: str
    language: str = "python"

class ExplainResponse(BaseModel):
    steps: list[str]
    narration: str

class ExplainSymbolRequest(BaseModel):
    code: str
    language: str = "python"
    symbol: str = ""
    kind: str = ""

class ExplainSymbolResponse(BaseModel):
    summary: str
    details: list[str] = []

class FixPythonErrorRequest(BaseModel):
    code: str
    error: str

class FixPythonErrorResponse(BaseModel):
    content: str
    summary: str