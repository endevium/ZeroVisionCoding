from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any

class EnqueueCommandRequest(BaseModel):
    type: str = Field(..., description="Command type, e.g. run_program, move_to_line")
    payload: dict[str, Any] = Field(default_factory=dict)

class EnqueueCommandResponse(BaseModel):
    id: str
    type: str
    payload: dict[str, Any]

class NextCommandResponse(BaseModel):
    id: str
    type: str
    payload: dict[str, Any]

class CommandResultRequest(BaseModel):
    id: str
    ok: bool
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)

class CommandResultResponse(BaseModel):
    id: str
    ok: bool
    message: str
    data: dict[str, Any]