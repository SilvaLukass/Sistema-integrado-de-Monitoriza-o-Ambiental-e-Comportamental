from __future__ import annotations

import itertools
from dataclasses import dataclass


@dataclass(frozen=True)
class SensorSnapshot:
    door_open: int
    motion_detected: int
    temp_c: float
    humidity: float


class MockSensorReader:
    """Deterministic reader for development without GPIO hardware."""

    def __init__(self) -> None:
        self._door_cycle = itertools.cycle([0, 0, 0, 1])
        self._motion_cycle = itertools.cycle([0, 1, 0, 0])
        self._temp_cycle = itertools.cycle([21.8, 22.0, 22.2, 22.1])
        self._humidity_cycle = itertools.cycle([47.0, 47.5, 48.0, 48.4])

    def read(self) -> SensorSnapshot:
        return SensorSnapshot(
            door_open=next(self._door_cycle),
            motion_detected=next(self._motion_cycle),
            temp_c=next(self._temp_cycle),
            humidity=next(self._humidity_cycle),
        )


class RpiSensorReader:
    """Read the magnetic door sensor, PIR, and AM2320 sensor."""

    def __init__(
        self,
        door_pin: int = 23,
        pir_pin: int = 17,
        dht_pin: str = "D4",
        door_active_high: bool = True,
    ) -> None:
        try:
            import RPi.GPIO as GPIO
            import adafruit_am2320
            import board
            import digitalio
        except ImportError as exc:
            raise RuntimeError(
                "Dependencias GPIO em falta. Instale rpi_agent/requirements.txt "
                "no Raspberry Pi ou use --mock fora do RPi."
            ) from exc

        door_board_pin = getattr(board, f"D{door_pin}", None)
        if door_board_pin is None:
            raise ValueError(f"Pino magnetico invalido: D{door_pin}")

        self._door = digitalio.DigitalInOut(door_board_pin)
        self._door.direction = digitalio.Direction.INPUT
        self._door.pull = digitalio.Pull.UP
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pir_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self._gpio = GPIO
        self._pir_pin = pir_pin
        self._am2320 = adafruit_am2320.AM2320(board.I2C())
        self._door_active_high = door_active_high

    def read(self) -> SensorSnapshot:
        door_value = bool(self._door.value)
        door_open = door_value if self._door_active_high else not door_value
        motion_detected = bool(self._gpio.input(self._pir_pin))
        temperature = self._am2320.temperature
        humidity = self._am2320.relative_humidity
        if temperature is None or humidity is None:
            raise RuntimeError("AM2320 nao devolveu temperatura/humidade.")
        return SensorSnapshot(
            door_open=1 if door_open else 0,
            motion_detected=1 if motion_detected else 0,
            temp_c=float(temperature),
            humidity=float(humidity),
        )
