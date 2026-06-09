from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..services.metrics import RpiMetricsError, fetch_rpi_metrics

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/rpi-metrics")
async def get_rpi_metrics(request: Request):
    settings = request.app.state.settings
    try:
        metrics = await fetch_rpi_metrics(settings)
    except RpiMetricsError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"online": True, **metrics}
