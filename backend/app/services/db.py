from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..models import Alert, ModelInferenceResponse, OccupancyHeatmapCell


MOTION_SENSOR_ROOMS = {
    "M001": "Sala de Estar",
    "M003": "Quarto",
    "M004": "Casa de Banho",
    "M018": "Cozinha",
}

DEVICE_SEED = [
    ("M001", "PIR - Sala de Estar", "Sala de Estar", "pir"),
    ("M003", "PIR - Quarto", "Quarto", "pir"),
    ("M004", "PIR - Casa de Banho", "Casa de Banho", "pir"),
    ("M018", "PIR - Cozinha", "Cozinha", "pir"),
    ("D001", "Porta - Entrada Principal", "Entrada Principal", "door"),
    ("T001", "Temperatura - Sala", "Sala de Estar", "temperature"),
    ("H001", "Humidade - Sala", "Sala de Estar", "humidity"),
    ("CO2", "Sensor CO2 - Sala", "Sala de Estar", "airQuality"),
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    """Small SQLite repository used by the API.

    The frontend should not care whether data came from the simulator today or
    from the Raspberry Pi later. This class stores the common persisted shape.
    """

    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._migrate()
        self.seed_devices()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _execute(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self._conn.execute(sql, params)
            self._conn.commit()
            return cur

    def _migrate(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    source TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS inferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    day INTEGER NOT NULL,
                    hour INTEGER NOT NULL,
                    expected_activity TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    is_anomaly INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    alert_created INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    ts TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    resolved INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    room TEXT NOT NULL,
                    type TEXT NOT NULL,
                    last_seen TEXT,
                    battery INTEGER NOT NULL DEFAULT 100,
                    online INTEGER NOT NULL DEFAULT 0,
                    last_value TEXT
                );
                """
            )
            self._conn.commit()

    def seed_devices(self) -> None:
        for device_id, name, room, device_type in DEVICE_SEED:
            self._execute(
                """
                INSERT OR IGNORE INTO devices (id, name, room, type, battery, online)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (device_id, name, room, device_type, 100),
            )

    def add_alert(self, alert: Alert) -> None:
        self._execute(
            """
            INSERT OR REPLACE INTO alerts (id, ts, title, description, severity, resolved)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (alert.id, alert.timestamp, alert.title, alert.description, alert.severity, int(alert.resolved)),
        )

    def list_alerts(self, limit: int = 500) -> list[Alert]:
        rows = self._conn.execute(
            """
            SELECT id, ts, title, description, severity, resolved
            FROM alerts
            ORDER BY ts DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            Alert(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                severity=row["severity"],
                timestamp=row["ts"],
                resolved=bool(row["resolved"]),
            )
            for row in rows
        ]

    def add_sensor_reading(self, readings: dict[str, float], source: str = "simulator") -> str:
        ts = utc_now_iso()
        self._execute(
            "INSERT INTO sensor_readings (ts, source, payload_json) VALUES (?, ?, ?)",
            (ts, source, json.dumps(readings)),
        )
        self.update_devices_from_reading(readings, ts)
        return ts

    def latest_sensor_reading(self) -> tuple[str, dict[str, float]] | None:
        row = self._conn.execute(
            "SELECT ts, payload_json FROM sensor_readings ORDER BY ts DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return row["ts"], json.loads(row["payload_json"])

    def list_sensor_readings_since(self, hours: int) -> list[tuple[str, dict[str, float]]]:
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        rows = self._conn.execute(
            """
            SELECT ts, payload_json
            FROM sensor_readings
            WHERE ts >= ?
            ORDER BY ts ASC
            """,
            (since,),
        ).fetchall()
        return [(row["ts"], json.loads(row["payload_json"])) for row in rows]

    def add_inference(self, response: ModelInferenceResponse, day: int, hour: int) -> None:
        self._execute(
            """
            INSERT INTO inferences (
                ts, day, hour, expected_activity, confidence, is_anomaly, reason, alert_created
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                utc_now_iso(),
                day,
                hour,
                response.expected_activity,
                response.confidence,
                int(response.is_anomaly),
                response.reason,
                int(response.alert_created),
            ),
        )

    def latest_inference(self) -> ModelInferenceResponse | None:
        row = self._conn.execute(
            """
            SELECT expected_activity, confidence, is_anomaly, reason, alert_created
            FROM inferences
            ORDER BY ts DESC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            return None
        return ModelInferenceResponse(
            expected_activity=row["expected_activity"],
            confidence=float(row["confidence"]),
            is_anomaly=bool(row["is_anomaly"]),
            reason=row["reason"],
            alert_created=bool(row["alert_created"]),
        )

    def occupancy_heatmap(self) -> list[OccupancyHeatmapCell]:
        rows = self._conn.execute(
            """
            SELECT day, hour, AVG(confidence) AS avg_confidence
            FROM inferences
            GROUP BY day, hour
            """
        ).fetchall()
        lookup = {(int(row["day"]), int(row["hour"])): int(round(row["avg_confidence"])) for row in rows}
        return [
            OccupancyHeatmapCell(day=day, hour=hour, value=lookup.get((day, hour), 0))
            for day in range(7)
            for hour in range(24)
        ]

    def update_devices_from_reading(self, readings: dict[str, float], ts: str) -> None:
        for device_id, value in readings.items():
            if device_id in {"hour", "minute", "day_of_week"}:
                continue
            self._execute(
                """
                INSERT INTO devices (id, name, room, type, last_seen, battery, online, last_value)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(id) DO UPDATE SET
                    last_seen = excluded.last_seen,
                    online = 1,
                    last_value = excluded.last_value
                """,
                (
                    device_id,
                    device_id,
                    MOTION_SENSOR_ROOMS.get(device_id, "Casa"),
                    "sensor",
                    ts,
                    100,
                    str(value),
                ),
            )

    def list_devices(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT id, name, room, type, last_seen, battery, online, last_value
            FROM devices
            ORDER BY id
            """
        ).fetchall()
        now = datetime.now(timezone.utc)
        devices: list[dict[str, Any]] = []
        for row in rows:
            last_seen = row["last_seen"]
            online = False
            if last_seen:
                dt = datetime.fromisoformat(last_seen)
                online = (now - dt.astimezone(timezone.utc)) < timedelta(seconds=90)
            devices.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "room": row["room"],
                    "type": row["type"],
                    "online": online,
                    "battery": int(row["battery"]),
                    "last_seen": last_seen,
                    "last_value": row["last_value"],
                }
            )
        return devices

    def sensor_history(self, hours: int = 24) -> list[dict[str, Any]]:
        readings = self.list_sensor_readings_since(hours)
        buckets: dict[int, list[dict[str, float]]] = {hour: [] for hour in range(24)}
        for ts, payload in readings:
            dt = datetime.fromisoformat(ts).astimezone(timezone.utc)
            buckets[dt.hour].append(payload)

        result: list[dict[str, Any]] = []
        for hour in range(24):
            values = buckets[hour]
            if not values:
                result.append(
                    {
                        "time": f"{hour:02d}:00",
                        "movement": 0,
                        "tempHum": 0,
                        "co2": 0,
                    }
                )
                continue

            movement_values = [
                max(float(reading.get(sensor, 0.0)) for sensor in MOTION_SENSOR_ROOMS)
                for reading in values
            ]
            temp_values = [float(reading.get("T001", 0.0)) for reading in values if "T001" in reading]
            co2_values = [float(reading.get("CO2", 0.0)) for reading in values if "CO2" in reading]
            result.append(
                {
                    "time": f"{hour:02d}:00",
                    "movement": int(round((sum(movement_values) / len(movement_values)) * 100)),
                    "tempHum": int(round(sum(temp_values) / len(temp_values))) if temp_values else 0,
                    "co2": int(round(sum(co2_values) / len(co2_values))) if co2_values else 0,
                }
            )
        return result

    def recent_activity(self, limit: int = 4) -> list[dict[str, str]]:
        rows = self._conn.execute(
            """
            SELECT ts, payload_json
            FROM sensor_readings
            ORDER BY ts DESC
            LIMIT 200
            """
        ).fetchall()
        events: list[dict[str, str]] = []
        last_motion: dict[str, int] = {sensor: 0 for sensor in MOTION_SENSOR_ROOMS}
        last_door: int | None = None

        for row in reversed(rows):
            payload = json.loads(row["payload_json"])
            dt = datetime.fromisoformat(row["ts"]).astimezone(timezone.utc)
            timestamp = dt.isoformat()

            for sensor, room in MOTION_SENSOR_ROOMS.items():
                value = int(float(payload.get(sensor, 0.0)) > 0)
                if value == 1 and last_motion[sensor] == 0:
                    events.append(
                        {
                            "room": room,
                            "timestamp": timestamp,
                            "description": "Movimento detetado",
                            "sensorLabel": "PIR",
                            "sensorColor": "blue",
                        }
                    )
                last_motion[sensor] = value

            if "D001" in payload:
                door_value = int(float(payload.get("D001", 0.0)) > 0)
                if last_door is not None:
                    if door_value == 1 and last_door == 0:
                        events.append(
                            {
                                "room": "Entrada Principal",
                                "timestamp": timestamp,
                                "description": "Porta aberta",
                                "sensorLabel": "Porta",
                                "sensorColor": "purple",
                            }
                        )
                    elif door_value == 0 and last_door == 1:
                        events.append(
                            {
                                "room": "Entrada Principal",
                                "timestamp": timestamp,
                                "description": "Porta fechada",
                                "sensorLabel": "Porta",
                                "sensorColor": "purple",
                            }
                        )
                last_door = door_value

        return list(reversed(events[-limit:]))


def init_db(db_path: Path) -> Database:
    return Database(db_path)
