from __future__ import annotations
from pydantic import BaseModel
from typing import Literal

class ReviewCodeRequest(BaseModel):
    code: str
    language: str = "python"

class ReviewCodeFromEditor(BaseModel):
    useActiveEditor: bool = True

class ReviewIssue(BaseModel):
    severity: Literal["Critical", "High", "Medium", "Low"]
    location: str
    explanation: str
    impact: str
    recommendation: str

class ReviewCodeResponse(BaseModel):
    overall_summary: str
    strengths: list[str]
    issues: list[ReviewIssue]
    final_assessment: str
    narration: str