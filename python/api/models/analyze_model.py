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