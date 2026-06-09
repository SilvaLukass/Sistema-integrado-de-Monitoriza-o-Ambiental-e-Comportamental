"""Small Flask service exposing Raspberry Pi host metrics.

Run this on the Raspberry Pi. The backend polls GET /metrics to show CPU,
memory, SoC temperature, and uptime on the device status dashboard.
"""

from __future__ import annotations

import time
from pathlib import Path

import psutil
from flask import Flask, jsonify

app = Flask(__name__)


def read_cpu_temperature_c() -> float | None:
    thermal_path = Path("/sys/class/thermal/thermal_zone0/temp")
    if not thermal_path.is_file():
        return None

    try:
        return int(thermal_path.read_text().strip()) / 1000.0
    except (OSError, ValueError):
        return None


@app.route("/metrics", methods=["GET"])
def metrics():
    memory = psutil.virtual_memory()
    uptime_seconds = max(0.0, time.time() - psutil.boot_time())
    temperature = read_cpu_temperature_c()

    return jsonify(
        {
            "cpu_percent": round(psutil.cpu_percent(interval=0.1), 1),
            "memory_percent": round(memory.percent, 1),
            "temperature_c": round(temperature, 1) if temperature is not None else None,
            "uptime_seconds": int(uptime_seconds),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
