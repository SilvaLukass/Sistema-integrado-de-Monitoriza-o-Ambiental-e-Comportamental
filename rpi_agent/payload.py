from __future__ import annotations

from datetime import datetime


def build_payload(
    door_open: int,
    temp_c: float,
    humidity: float,
    now: datetime | None = None,
) -> dict[str, float]:
    """Build the readings contract consumed by the backend RabbitMQ consumer."""
    current = now or datetime.now()
    return {
        "hour": float(current.hour),
        "day_of_week": float(current.weekday()),
        "minute": float(current.minute),
        "D001": float(door_open),
        "T001": round(float(temp_c), 1),
        "H001": round(float(humidity), 1),
    }
