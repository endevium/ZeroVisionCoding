from fastapi import APIRouter, HTTPException
from api.models.analyze_model import *
from api.controllers.analyze_controller import *
from api.services.extension_state import *
from api.services.editor_state import *
from api.models.analyze_model import ChatRequest, ChatResponse, AnalyzeRequest, ExplainResponse
from api.controllers.analyze_controller import chat_controller, analyze_code_controller, analyze_active_editor_controller
from api.models.commands_model import EnqueueCommandRequest, EnqueueCommandResponse, NextCommandResponse, CommandResultRequest, CommandResultResponse
from api.services.command_queue import QUEUE
from api.services import terminal_state

router = APIRouter()

@router.get("/")
def status_check():
    return {"status": "Zero Vision Coding server is running"}

@router.post("/vscode/register")
def vscode_register(payload: dict):
    name = payload.get("name")
    version = payload.get("version")
    return register_extension(name=name, version=version)

@router.get("/vscode/status")
def vscode_status():
    return get_status()

@router.post("/vscode/editor")
def vscode_editor(payload: dict):
    return update_editor(payload)

@router.get("/vscode/editor")
def vscode_editor_get():
    return get_editor()



@router.post("/chat", response_model=ChatResponse)
def llm_chat(req: ChatRequest):
    return chat_controller(req.message)

@router.post("/analyze", response_model=ExplainResponse)
def llm_analyze(req: AnalyzeRequest):
    return analyze_code_controller(req.code, req.language)

@router.post("/analyze-active-editor", response_model=ExplainResponse)
def llm_analyze_active_editor():
    return analyze_active_editor_controller()



@router.post("/vscode/command", response_model=EnqueueCommandResponse)
def enqueue_vscode_command(req: EnqueueCommandRequest):
    item = QUEUE.enqueue(req.type, req.payload)
    return {"id": item.id, "type": item.type, "payload": item.payload}

@router.get("/vscode/next-command", response_model=NextCommandResponse)
def next_vscode_command():
    item = QUEUE.next()
    if not item:
        raise HTTPException(status_code=204, detail="No commands")
    return {"id": item.id, "type": item.type, "payload": item.payload}

@router.post("/vscode/command-result", response_model=CommandResultResponse)
def vscode_command_result(req: CommandResultRequest):
    QUEUE.set_result(req.id, req.ok, req.message, req.data)
    return {"id": req.id, "ok": req.ok, "message": req.message, "data": req.data}

@router.get("/vscode/command-result/{command_id}", response_model=CommandResultResponse)
def get_vscode_command_result(command_id: str):
    res = QUEUE.get_result(command_id)
    if not res:
        raise HTTPException(status_code=404, detail="No result yet")
    return res



@router.post("/terminal/reset")
def terminal_reset(payload: dict):
    terminal_state.reset(str(payload.get("command") or ""))
    return {"ok": True}

@router.post("/terminal/append")
def terminal_append(payload: dict):
    terminal_state.append(
        stdout=str(payload.get("stdout") or ""),
        stderr=str(payload.get("stderr") or "")
    )
    return {"ok": True}

@router.post("/terminal/finish")
def terminal_finish(payload: dict):
    code = payload.get("exit_code")
    try:
        code_i = int(code)
    except Exception:
        code_i = 0
    terminal_state.finish(code_i)
    return {"ok": True}

@router.get("/terminal/snapshot")
def terminal_snapshot():
    return terminal_state.snapshot()