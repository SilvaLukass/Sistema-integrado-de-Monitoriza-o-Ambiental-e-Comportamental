from __future__ import annotations

import os
import time

from fastapi import APIRouter

from ..models import SystemMetrics

router = APIRouter()
STARTED_AT = time.time()

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover - fallback keeps endpoint alive without psutil.
    psutil = None


def _temperature_best_effort() -> float | None:
    if psutil is None or not hasattr(psutil, "sensors_temperatures"):
        return None

    try:
        temps = psutil.sensors_temperatures()
    except Exception:
        return None

    for entries in temps.values():
        if entries:
            return float(entries[0].current)
    return None


@router.get("/api/system/metrics", response_model=SystemMetrics)
async def system_metrics():
    if psutil is not None:
        try:
            uptime_seconds = int(time.time() - psutil.boot_time())
        except Exception:
            uptime_seconds = int(time.time() - STARTED_AT)

        return SystemMetrics(
            cpu_usage=float(psutil.cpu_percent(interval=None)),
            memory_usage=float(psutil.virtual_memory().percent),
            temperature=_temperature_best_effort(),
            uptime_seconds=uptime_seconds,
            source="psutil",
        )

    load = os.getloadavg()[0] if hasattr(os, "getloadavg") else 0.0
    return SystemMetrics(
        cpu_usage=min(load * 25, 100),
        memory_usage=0,
        temperature=None,
        uptime_seconds=int(time.time() - STARTED_AT),
        source="stdlib-fallback",
        extra={"load_avg_1m": load},
    )
