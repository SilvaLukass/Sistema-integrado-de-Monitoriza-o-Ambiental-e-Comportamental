from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

import pika
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection


@dataclass
class RabbitMqPublisher:
    broker_url: str
    exchange: str = "eldercare.sensors"
    routing_key: str = "sensors.rpi"
    reconnect_delay_seconds: float = 3.0

    def __post_init__(self) -> None:
        self._connection: BlockingConnection | None = None
        self._channel: BlockingChannel | None = None

    def close(self) -> None:
        if self._connection is not None and self._connection.is_open:
            self._connection.close()
        self._connection = None
        self._channel = None

    def _connect(self) -> BlockingChannel:
        if self._channel is not None and self._channel.is_open:
            return self._channel

        parameters = pika.URLParameters(self.broker_url)
        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()
        self._channel.exchange_declare(
            exchange=self.exchange,
            exchange_type="topic",
            durable=True,
        )
        return self._channel

    def publish(
        self,
        readings: dict[str, float],
        source: str = "rpi",
        attempts: int = 3,
    ) -> None:
        payload: dict[str, Any] = {"source": source, "readings": readings}
        body = json.dumps(payload).encode("utf-8")
        properties = pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
        )

        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                channel = self._connect()
                channel.basic_publish(
                    exchange=self.exchange,
                    routing_key=self.routing_key,
                    body=body,
                    properties=properties,
                )
                return
            except pika.exceptions.AMQPError as exc:
                last_error = exc
                self.close()
                if attempt < attempts:
                    time.sleep(self.reconnect_delay_seconds)

        if last_error is not None:
            raise last_error
