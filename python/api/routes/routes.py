from fastapi import APIRouter
from api.models.analyze_model import *
from api.controllers.analyze_controller import *
from api.services.extension_state import *
from api.services.editor_state import *

router = APIRouter()

@router.get("/")
def status_check():
    return {"status": "Zero Vision Coding server is running"}

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_code(req: AnalyzeRequest):
    return analyze_code_controller(req.code, req.language)

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