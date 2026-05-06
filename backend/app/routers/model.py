from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import numpy as np
import pandas as pd

from fastapi import APIRouter, HTTPException, Request

from ..models import (
    AlertCreate,
    ModelInferenceRequest,
    ModelInferenceResponse,
    OccupancyHeatmapCell,
)
from .alerts import create_and_notify_alert_from_app
from ..services.aruba_dataset import aruba_occupancy_heatmap
from ..services.sensor_filter import data_validation

router = APIRouter()

CONFIDENCE_THRESHOLD = 30.0
ALERT_COOLDOWN_MINUTES = 10


def _predict_from_model(
    readings: dict[str, float],
    feature_cols: list[str],
    model: Any,
    label_mapping: dict[str, int],
) -> tuple[str, float]:
    now = datetime.now()
    row: dict[str, float] = {}
    for col in feature_cols:
        if col == "hour":
            row[col] = float(readings.get("hour", now.hour))
        elif col == "day_of_week":
            row[col] = float(readings.get("day_of_week", now.weekday()))
        elif col == "minute":
            row[col] = float(readings.get("minute", now.minute))
        else:
            row[col] = float(readings.get(col, 0.0))

    x = pd.DataFrame([[row[col] for col in feature_cols]], columns=feature_cols, dtype=float)
    proba = model.predict_proba(x)[0]
    best_idx = int(np.argmax(proba))
    confidence = float(proba[best_idx] * 100.0)
    predicted_label = int(model.classes_[best_idx])
    inv_mapping = {v: k for k, v in label_mapping.items()}
    expected_activity = inv_mapping.get(predicted_label, f"label_{predicted_label}")
    return expected_activity, confidence


def _build_heatmap(store: list[dict[str, Any]]) -> list[OccupancyHeatmapCell]:
    buckets: dict[tuple[int, int], list[float]] = {}
    for item in store:
        day = int(item["day"])
        hour = int(item["hour"])
        buckets.setdefault((day, hour), []).append(float(item["confidence"]))

    result: list[OccupancyHeatmapCell] = []
    for day in range(7):
        for hour in range(24):
            values = buckets.get((day, hour), [])
            avg = int(round(sum(values) / len(values))) if values else 0
            result.append(OccupancyHeatmapCell(day=day, hour=hour, value=avg))
    return result


async def process_model_readings(app, readings: dict[str, float], persist: bool = True) -> ModelInferenceResponse:
    """Run the active ML model against one reading snapshot.

    This function is intentionally independent from HTTP so the simulator,
    Raspberry Pi ingest endpoint, and manual debug endpoint can share exactly
    the same inference path.
    """
    app.state.latest_sensor_data = readings

    imidiate_Alert = data_validation(readings)
    now = datetime.now(timezone.utc)
    hour = int(readings.get("hour", now.hour))
    day = int(readings.get("day_of_week", now.weekday()))

    if imidiate_Alert:
        result = await create_and_notify_alert_from_app(
            AlertCreate(
                title="Alerta imediato: " + imidiate_Alert,
                description=(
                    f"Valor anormal detetado no sensor. "
                    f"Motivo: {imidiate_Alert}."
                ),
                severity="danger",
            ),
            app,
        )
        response = ModelInferenceResponse(
            expected_activity="Anomalia detectada",
            confidence=0.0,
            is_anomaly=True,
            reason=imidiate_Alert,
            alert_created=result.alert.id != "",
        )
        if persist:
            app.state.db.add_inference(response, day=day, hour=hour)
        return response

    model = getattr(app.state, "ml_model", None)
    feature_cols = getattr(app.state, "ml_features", None)
    label_mapping = getattr(app.state, "ml_label_mapping", None)
    if model is None or feature_cols is None or label_mapping is None:
        raise HTTPException(status_code=503, detail="Modelo nao carregado no backend.")

    activity, confidence = _predict_from_model(
        readings, feature_cols, model, label_mapping
    )
    is_anomaly = confidence < CONFIDENCE_THRESHOLD
    reason = "confianca da previsao abaixo do limiar" if is_anomaly else "padrao comportamental esperado"

    alert_created = False
    if confidence < CONFIDENCE_THRESHOLD:
        last_alert_at = getattr(app.state, "last_low_confidence_alert_at", None)
        should_alert = (
            last_alert_at is None
            or now - last_alert_at >= timedelta(minutes=ALERT_COOLDOWN_MINUTES)
        )
        if should_alert:
            result = await create_and_notify_alert_from_app(
                AlertCreate(
                    title="Possivel situacao de risco",
                    description=(
                        f"Confianca do modelo abaixo de {CONFIDENCE_THRESHOLD:.0f}% "
                        f"({confidence:.1f}%). Motivo: {reason}."
                    ),
                    severity="danger",
                ),
                app,
            )
            alert_created = result.alert.id != ""
            app.state.last_low_confidence_alert_at = now

    response = ModelInferenceResponse(
        expected_activity=activity,
        confidence=confidence,
        is_anomaly=is_anomaly,
        reason=reason,
        alert_created=alert_created,
    )
    if persist:
        app.state.db.add_inference(response, day=day, hour=hour)
    return response


@router.post("/api/model/infer", response_model=ModelInferenceResponse)
async def infer_model(payload: ModelInferenceRequest, request: Request):
    return await process_model_readings(request.app, payload.readings)


@router.get("/api/model/latest", response_model=ModelInferenceResponse)
async def latest_model_inference(request: Request):
    latest = request.app.state.db.latest_inference()
    if latest is None:
        raise HTTPException(status_code=404, detail="Ainda nao existem inferencias.")
    return latest


@router.get("/api/model/occupancy-heatmap", response_model=list[OccupancyHeatmapCell])
async def occupancy_heatmap(request: Request):
    project_root = getattr(request.app.state, "project_root", None)
    if project_root is not None:
        return aruba_occupancy_heatmap(str(project_root))

    db = getattr(request.app.state, "db", None)
    if db is not None:
        return db.occupancy_heatmap()

    store = request.app.state.model_inference_store
    return _build_heatmap(list(store))
