from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from ..models import OccupancyHeatmapCell

MOTION_PREFIX = "M"
TEMPERATURE_PREFIX = "T"


def _parse_aruba_file(path: Path) -> pd.DataFrame:
    """Load the Aruba CASAS dataset in its raw event format.

    The file is event-based: each row is one sensor event, not one complete
    sensor snapshot. That means historical charts must aggregate events over
    time instead of reading one ready-made row per minute.
    """
    raw = pd.read_csv(
        path,
        sep=r"\s+",
        names=["date", "time", "sensor", "value", "label", "status"],
        engine="python",
    )
    raw["dt"] = pd.to_datetime(raw["date"].astype(str) + " " + raw["time"].astype(str), errors="coerce")
    raw = raw.dropna(subset=["dt"])
    raw["hour"] = raw["dt"].dt.hour
    raw["day"] = raw["dt"].dt.weekday
    raw["numeric_value"] = raw["value"].map({"ON": 1.0, "OFF": 0.0}).fillna(pd.to_numeric(raw["value"], errors="coerce"))
    return raw[["dt", "day", "hour", "sensor", "value", "numeric_value", "label"]]


@lru_cache(maxsize=1)
def load_aruba_dataset(project_root: str) -> pd.DataFrame:
    root = Path(project_root)
    candidates = [root / "aruba.txt", root / "new_labeled_data" / "aruba.txt"]
    dataset_path = next((path for path in candidates if path.exists()), None)
    if dataset_path is None:
        raise FileNotFoundError("Nao foi encontrado aruba.txt nem new_labeled_data/aruba.txt")
    return _parse_aruba_file(dataset_path)


def aruba_sensor_history(project_root: str) -> list[dict[str, Any]]:
    df = load_aruba_dataset(project_root)

    motion = df[df["sensor"].str.startswith(MOTION_PREFIX, na=False)].copy()
    motion_on = motion[motion["numeric_value"] > 0]
    motion_counts = motion_on.groupby("hour").size()
    max_motion = float(motion_counts.max()) if not motion_counts.empty else 1.0

    temp = df[df["sensor"].str.startswith(TEMPERATURE_PREFIX, na=False)].copy()
    temp_by_hour = temp.groupby("hour")["numeric_value"].mean()

    # Aruba has no CO2/air-quality sensor, so CO2 must be absent rather than
    # filled with fake data. The frontend can then explain that honestly.
    return [
        {
            "time": f"{hour:02d}:00",
            "movement": int(round((float(motion_counts.get(hour, 0)) / max_motion) * 100)),
            "tempHum": int(round(float(temp_by_hour.get(hour, 0)))) if hour in temp_by_hour else 0,
            "co2": None,
        }
        for hour in range(24)
    ]


def aruba_occupancy_heatmap(project_root: str) -> list[OccupancyHeatmapCell]:
    df = load_aruba_dataset(project_root)
    motion_on = df[
        df["sensor"].str.startswith(MOTION_PREFIX, na=False)
        & (df["numeric_value"] > 0)
    ]
    grouped = motion_on.groupby(["day", "hour"]).size()
    max_count = float(grouped.max()) if not grouped.empty else 1.0

    return [
        OccupancyHeatmapCell(
            day=day,
            hour=hour,
            value=int(round((float(grouped.get((day, hour), 0)) / max_count) * 100)),
        )
        for day in range(7)
        for hour in range(24)
    ]
