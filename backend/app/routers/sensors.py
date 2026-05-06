from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from ..models import (
    ActivityEvent,
    LatestSensorsResponse,
    ModelInferenceResponse,
    SensorHistoryPoint,
    SensorIngestRequest,
)
from ..services.aruba_dataset import aruba_sensor_history
from ..services.co2_model import co2_status
from ..services.db import MOTION_SENSOR_ROOMS
from .model import process_model_readings

router = APIRouter()

def _last_activity_room(readings: dict[str, float]) -> str | None:
    for sensor_id, room in MOTION_SENSOR_ROOMS.items():
        if float(readings.get(sensor_id, 0.0)) > 0:
            return room
    if float(readings.get("D001", 0.0)) > 0:
        return "Entrada Principal"
    return None


@router.post("/api/sensors/ingest", response_model=ModelInferenceResponse)
async def ingest_sensor_reading(payload: SensorIngestRequest, request: Request):
    """Persist one sensor snapshot and immediately run the ML model.

    The Raspberry Pi can call this same endpoint later. For now, the backend
    simulator feeds it with realistic readings.
    """
    request.app.state.db.add_sensor_reading(payload.readings, source=payload.source)
    return await process_model_readings(request.app, payload.readings)


@router.get("/api/sensors/latest", response_model=LatestSensorsResponse)
async def latest_sensor_reading(request: Request):
    latest = request.app.state.db.latest_sensor_reading()
    if latest is None:
        raise HTTPException(status_code=404, detail="Ainda nao existem leituras.")

    timestamp, readings = latest
    co2 = float(readings.get("CO2", 0.0))
    temperature = float(readings.get("T001", 0.0))
    return LatestSensorsResponse(
        timestamp=timestamp,
        readings=readings,
        co2=co2,
        co2_status=co2_status(co2),
        temperature=temperature,
        last_activity_room=_last_activity_room(readings),
    )


@router.get("/api/sensors/history", response_model=list[SensorHistoryPoint])
async def sensor_history(request: Request, hours: int = Query(default=24, ge=1, le=168)):
    return aruba_sensor_history(str(request.app.state.project_root))


@router.get("/api/activity/recent", response_model=list[ActivityEvent])
async def recent_activity(request: Request):
    return request.app.state.db.recent_activity()
