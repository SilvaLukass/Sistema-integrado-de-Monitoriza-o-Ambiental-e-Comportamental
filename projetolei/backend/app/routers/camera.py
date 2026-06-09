from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..services.camera import CameraCaptureError, capture_frame

router = APIRouter(prefix="/api/camera", tags=["camera"])


@router.post("/capture")
async def capture_camera_frame(request: Request):
    settings = request.app.state.settings
    try:
        frame = await capture_frame(settings)
    except CameraCaptureError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return StreamingResponse(BytesIO(frame), media_type="image/jpeg")
