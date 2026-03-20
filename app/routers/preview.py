# Preview Server Router

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ..preview import preview_manager

router = APIRouter()

class PreviewStartRequest(BaseModel):
    project_id: str
    project_path: str
    command: Optional[str] = None
    port: Optional[int] = None

class PreviewStartResponse(BaseModel):
    success: bool
    preview_url: Optional[str] = None
    port: int
    process_id: Optional[str] = None
    error: Optional[str] = None

class PreviewStopRequest(BaseModel):
    project_id: str

class PreviewStopResponse(BaseModel):
    success: bool
    message: str

@router.post("/start", response_model=PreviewStartResponse)
async def start_preview(request: PreviewStartRequest):
    """Start a preview server for a project."""
    result = await preview_manager.start_preview(
        project_id=request.project_id,
        project_path=request.project_path,
        command=request.command,
        port=request.port
    )
    return PreviewStartResponse(**result)

@router.post("/stop", response_model=PreviewStopResponse)
async def stop_preview(request: PreviewStopRequest):
    """Stop a preview server."""
    result = await preview_manager.stop_preview(request.project_id)
    return PreviewStopResponse(**result)

@router.get("/active")
async def get_active_previews():
    """Get all active preview servers."""
    return preview_manager.get_active_previews()
