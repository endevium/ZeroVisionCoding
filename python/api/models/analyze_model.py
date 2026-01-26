from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    code: str
    language: str = "python"

class AnalyzeResponse(BaseModel):
    language: str
    issues: list[str]
    message: str