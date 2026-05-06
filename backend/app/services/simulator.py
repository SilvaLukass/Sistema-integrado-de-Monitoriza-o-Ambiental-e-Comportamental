from __future__ import annotations

import asyncio
import math
import random
from datetime import datetime

from ..routers.model import process_model_readings


def build_simulated_readings(now: datetime | None = None) -> dict[str, float]:
    """Generate one realistic reading snapshot for local development.

    Later, the Raspberry Pi will send this same payload shape to
    `POST /api/sensors/ingest`. Keeping the shape identical is what lets the
    frontend stay unchanged when the real device arrives.
    """
    now = now or datetime.now()
    hour = now.hour
    minute = now.minute
    day_of_week = now.weekday()

    morning = 7 <= hour <= 10
    afternoon = 11 <= hour <= 16
    evening = 17 <= hour <= 21
    night = hour >= 23 or hour <= 6

    movement_base = 0.0
    if morning:
        movement_base = 0.8
    elif afternoon:
        movement_base = 0.35
    elif evening:
        movement_base = 0.75

    temp = 22 + math.sin((hour - 6) * (math.pi / 12)) * 3 + random.uniform(-0.6, 0.6)
    co2 = 430 + random.uniform(-35, 45)
    if hour in {13, 14}:
        co2 = 850 + random.uniform(0, 250)
    if hour in {19, 20}:
        co2 = 1250 + random.uniform(0, 300)

    return {
        "hour": float(hour),
        "day_of_week": float(day_of_week),
        "minute": float(minute),
        "M001": 1.0 if movement_base > 0.5 and random.random() < 0.55 else 0.0,
        "M003": 1.0 if night and random.random() < 0.8 else 0.0,
        "M004": 1.0 if random.random() < 0.04 else 0.0,
        "M018": 1.0 if (morning or evening) and random.random() < 0.45 else 0.0,
        "D001": 1.0 if random.random() < 0.02 else 0.0,
        "T001": round(temp, 1),
        "CO2": round(co2),
    }


async def simulator_loop(app, interval_seconds: int) -> None:
    while True:
        readings = build_simulated_readings()
        app.state.db.add_sensor_reading(readings, source="simulator")
        try:
            await process_model_readings(app, readings)
        except Exception as exc:
            print(f"Aviso: simulador nao conseguiu correr inferencia: {exc}")
        await asyncio.sleep(interval_seconds)


def start_simulator(app, interval_seconds: int) -> asyncio.Task:
    return asyncio.create_task(simulator_loop(app, interval_seconds))
