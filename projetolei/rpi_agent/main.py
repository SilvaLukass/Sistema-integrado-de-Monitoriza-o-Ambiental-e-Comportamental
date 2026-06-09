from __future__ import annotations

import argparse
import logging
import time

from .payload import build_payload
from .publisher import RabbitMqPublisher
from .sensor_reader import MockSensorReader, RpiSensorReader, SensorSnapshot

LOGGER = logging.getLogger("rpi_agent")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ElderCare Raspberry Pi sensor agent")
    parser.add_argument(
        "--broker-url",
        required=True,
        help="RabbitMQ URL, e.g. amqp://eldercare:password@192.168.1.10:5672/",
    )
    parser.add_argument("--exchange", default="eldercare.sensors")
    parser.add_argument("--routing-key", default="sensors.rpi")
    parser.add_argument("--source", default="rpi")
    parser.add_argument("--interval", type=float, default=10.0)
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    parser.add_argument("--door-pin", type=int, default=23)
    parser.add_argument("--pir-pin", type=int, default=17)
    parser.add_argument("--dht-pin", default="D4")
    parser.add_argument("--door-active-low", action="store_true")
    parser.add_argument("--mock", action="store_true")
    return parser.parse_args()


def build_reader(args: argparse.Namespace):
    if args.mock:
        return MockSensorReader()
    return RpiSensorReader(
        door_pin=args.door_pin,
        pir_pin=args.pir_pin,
        dht_pin=args.dht_pin,
        door_active_high=not args.door_active_low,
    )


def should_publish(
    snapshot: SensorSnapshot,
    last_publish_at: float,
    last_door_state: int | None,
    last_motion_state: int | None,
    interval_seconds: float,
) -> bool:
    if last_door_state is None or snapshot.door_open != last_door_state:
        return True
    if last_motion_state is None or snapshot.motion_detected != last_motion_state:
        return True
    return (time.monotonic() - last_publish_at) >= interval_seconds


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    reader = build_reader(args)
    publisher = RabbitMqPublisher(
        broker_url=args.broker_url,
        exchange=args.exchange,
        routing_key=args.routing_key,
    )

    last_publish_at = 0.0
    last_door_state: int | None = None
    last_motion_state: int | None = None
    LOGGER.info("RPi sensor agent started (source=%s, mock=%s)", args.source, args.mock)

    try:
        while True:
            try:
                snapshot = reader.read()
                if should_publish(
                    snapshot,
                    last_publish_at,
                    last_door_state,
                    last_motion_state,
                    args.interval,
                ):
                    readings = build_payload(
                        door_open=snapshot.door_open,
                        motion_detected=snapshot.motion_detected,
                        temp_c=snapshot.temp_c,
                        humidity=snapshot.humidity,
                    )
                    publisher.publish(readings, source=args.source)
                    last_publish_at = time.monotonic()
                    last_door_state = snapshot.door_open
                    last_motion_state = snapshot.motion_detected
                    LOGGER.info("Published readings: %s", readings)
            except Exception as exc:
                LOGGER.warning("Could not read/publish sensors: %s", exc)

            time.sleep(max(args.poll_seconds, 0.1))
    finally:
        publisher.close()


if __name__ == "__main__":
    main()
