from __future__ import annotations

import random

BASELINE_PPM = 420.0
GOOD_MAX_PPM = 800.0
MODERATE_MAX_PPM = 1200.0

MAX_PRODUCTION_PER_MIN = 8.5
DECAY_PER_MIN = 0.010
DOOR_VENT_PPM = 40.0
NOISE_STD = 3.0

MIN_CO2_PPM = 400.0
MAX_CO2_PPM = 2500.0


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def co2_status(ppm: float) -> str:
    """Map CO2 concentration (ppm) to the dashboard quality label."""
    if ppm <= GOOD_MAX_PPM:
        return "Bom"
    if ppm <= MODERATE_MAX_PPM:
        return "Moderado"
    return "Mau"


def co2_step(
    prev_ppm: float,
    motion_score: float,
    door_event: bool,
    dt_minutes: float,
    add_noise: bool = True,
) -> float:
    """Advance the indoor CO2 simulation one time step.

    The model is intentionally simple and stable:
    - production: rises with occupancy/motion intensity
    - decay: naturally returns to baseline over time
    - ventilation: an open door event quickly improves air quality
    """
    safe_dt = max(0.0, dt_minutes)
    safe_motion = _clamp(float(motion_score), 0.0, 1.0)
    current = float(prev_ppm)

    production = MAX_PRODUCTION_PER_MIN * safe_motion * safe_dt
    decay = (current - BASELINE_PPM) * DECAY_PER_MIN * safe_dt
    vent = DOOR_VENT_PPM if door_event else 0.0
    noise = random.gauss(0.0, NOISE_STD) if add_noise else 0.0

    next_ppm = current - decay - vent + production + noise
    return _clamp(next_ppm, MIN_CO2_PPM, MAX_CO2_PPM)
