from __future__ import annotations

import itertools
from dataclasses import dataclass


@dataclass(frozen=True)
class SensorSnapshot:
    door_open: int
    temp_c: float
    humidity: float


class MockSensorReader:
    """Deterministic reader for development without GPIO hardware."""

    def __init__(self) -> None:
        self._door_cycle = itertools.cycle([0, 0, 0, 1])
        self._temp_cycle = itertools.cycle([21.8, 22.0, 22.2, 22.1])
        self._humidity_cycle = itertools.cycle([47.0, 47.5, 48.0, 48.4])

    def read(self) -> SensorSnapshot:
        return SensorSnapshot(
            door_open=next(self._door_cycle),
            temp_c=next(self._temp_cycle),
            humidity=next(self._humidity_cycle),
        )


class RpiSensorReader:
    """Read the reed switch and DHT22 from Raspberry Pi GPIO pins."""

    def __init__(
        self,
        door_pin: int = 17,
        dht_pin: str = "D4",
        door_active_high: bool = True,
    ) -> None:
        try:
            from gpiozero import Button
            import adafruit_dht
            import board
        except ImportError as exc:
            raise RuntimeError(
                "Dependencias GPIO em falta. Instale rpi_agent/requirements.txt "
                "no Raspberry Pi ou use --mock fora do RPi."
            ) from exc

        board_pin = getattr(board, dht_pin, None)
        if board_pin is None:
            raise ValueError(f"Pino DHT22 invalido: {dht_pin}")

        self._door = Button(door_pin, pull_up=True)
        self._dht = adafruit_dht.DHT22(board_pin)
        self._door_active_high = door_active_high

    def read(self) -> SensorSnapshot:
        pressed = bool(self._door.is_pressed)
        door_open = pressed if self._door_active_high else not pressed
        return SensorSnapshot(
            door_open=1 if door_open else 0,
            temp_c=float(self._dht.temperature),
            humidity=float(self._dht.humidity),
        )
