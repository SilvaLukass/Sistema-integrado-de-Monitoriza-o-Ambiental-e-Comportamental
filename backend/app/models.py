from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

AlertSeverity = Literal["warning", "success", "info", "danger"]

class AlertCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=500)
    severity: AlertSeverity


class Alert(BaseModel):
    id: str
    title: str
    description: str
    severity: AlertSeverity
    timestamp: str
    resolved: bool

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


class AlertCreateResult(BaseModel):
    alert: Alert
    notification_sent: bool
    notification_error: Optional[str] = None


class ModelInferenceRequest(BaseModel):
    readings: dict[str, float] = Field(default_factory=dict)


class ModelInferenceResponse(BaseModel):
    expected_activity: str
    confidence: float = Field(ge=0, le=100)
    is_anomaly: bool
    reason: str
    alert_created: bool = False


class OccupancyHeatmapCell(BaseModel):
    day: int = Field(ge=0, le=6)
    hour: int = Field(ge=0, le=23)
    value: int = Field(ge=0, le=100)


class SensorIngestRequest(BaseModel):
    readings: dict[str, float] = Field(default_factory=dict)
    source: str = "simulator"


class LatestSensorsResponse(BaseModel):
    timestamp: str
    readings: dict[str, float]
    co2: float
    co2_status: str
    temperature: float
    last_activity_room: Optional[str] = None


class SensorHistoryPoint(BaseModel):
    time: str
    movement: int = Field(ge=0, le=100)
    tempHum: int = Field(ge=0)
    co2: Optional[int] = Field(default=None, ge=0)


class DeviceStatus(BaseModel):
    id: str
    name: str
    room: str
    type: str
    online: bool
    battery: int = Field(ge=0, le=100)
    last_seen: Optional[str] = None
    last_value: Optional[str] = None


class ActivityEvent(BaseModel):
    room: str
    time: str
    description: str
    sensorLabel: str
    sensorColor: Literal["blue", "purple"] = "blue"


class SystemMetrics(BaseModel):
    cpu_usage: float = Field(ge=0, le=100)
    memory_usage: float = Field(ge=0, le=100)
    temperature: Optional[float] = None
    uptime_seconds: int = Field(ge=0)
    source: str
    extra: dict[str, Any] = Field(default_factory=dict)
