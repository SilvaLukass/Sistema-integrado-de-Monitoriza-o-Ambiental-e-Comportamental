from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

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
