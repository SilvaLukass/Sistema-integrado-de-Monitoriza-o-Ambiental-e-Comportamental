from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

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
    resolved: bool = False

    @classmethod
    def from_create(cls, payload: AlertCreate) -> "Alert":
        return cls(
            id=str(uuid4()),
            title=payload.title,
            description=payload.description,
            severity=payload.severity,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


class AlertCreateResult(BaseModel):
    alert: Alert
    notification_sent: bool
    notification_error: str | None = None
