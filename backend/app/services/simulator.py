from __future__ import annotations

import asyncio
import math
import random
from datetime import datetime

from .co2_model import BASELINE_PPM, co2_step
from .messaging import publish_reading

SIMULATOR_START_CO2_PPM = 600.0


def _motion_score_from_readings(readings: dict[str, float]) -> float:
    motion_sensors = ["M001", "M003", "M004", "M018"]
    active = sum(1.0 for sensor in motion_sensors if float(readings.get(sensor, 0.0)) > 0.0)
    return active / float(len(motion_sensors))


def build_simulated_readings(now: datetime | None = None, co2_ppm: float | None = None) -> dict[str, float]:
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
    if co2_ppm is None:
        co2_ppm = BASELINE_PPM

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
        "CO2": round(co2_ppm),
    }


async def simulator_loop(app, interval_seconds: int) -> None:
    """Publisher simulado.

    O simulador deixou de tocar diretamente no modelo/BD: passou a publicar as
    leituras no broker RabbitMQ. O consumer do backend e que persiste e corre a
    inferencia. Isto exercita o caminho real publish -> consume -> modelo -> BD
    antes de existir hardware, e amanha o RPi substitui este publisher sem
    qualquer alteracao no backend.
    """
    if not hasattr(app.state, "simulator_state"):
        # Start slightly above outdoor baseline to better match typical indoor air.
        app.state.simulator_state = {"co2_ppm": SIMULATOR_START_CO2_PPM}

    settings = app.state.settings
    channel = None

    while True:
        previous_co2 = float(app.state.simulator_state.get("co2_ppm", BASELINE_PPM))
        readings = build_simulated_readings(co2_ppm=previous_co2)
        motion_score = _motion_score_from_readings(readings)
        door_event = float(readings.get("D001", 0.0)) > 0.0
        next_co2 = co2_step(
            prev_ppm=previous_co2,
            motion_score=motion_score,
            door_event=door_event,
            dt_minutes=max(interval_seconds / 60.0, 0.0),
            add_noise=True,
        )
        readings["CO2"] = round(next_co2)
        app.state.simulator_state["co2_ppm"] = next_co2

        try:
            connection = getattr(app.state, "rabbitmq", None)
            if connection is None:
                raise RuntimeError("ligacao RabbitMQ indisponivel")
            if channel is None or channel.is_closed:
                channel = await connection.channel()
            await publish_reading(
                channel,
                settings.rabbitmq_exchange,
                settings.rabbitmq_routing_key,
                source="simulator",
                readings=readings,
            )
        except Exception as exc:
            # Nao deixar o simulador morrer se o broker estiver em baixo; tenta
            # de novo na proxima iteracao (connect_robust reconecta sozinho).
            channel = None
            print(f"Aviso: simulador nao conseguiu publicar no broker: {exc}")

        await asyncio.sleep(interval_seconds)


def start_simulator(app, interval_seconds: int) -> asyncio.Task:
    return asyncio.create_task(simulator_loop(app, interval_seconds))
