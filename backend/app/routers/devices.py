from __future__ import annotations

from fastapi import APIRouter, Request

from ..models import DeviceStatus

router = APIRouter()


@router.get("/api/devices", response_model=list[DeviceStatus])
async def list_devices(request: Request):
    return request.app.state.db.list_devices()
