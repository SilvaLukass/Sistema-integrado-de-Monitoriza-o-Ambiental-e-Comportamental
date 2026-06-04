"""Camada de mensageria RabbitMQ (publish/subscribe) do ElderCare.

O objetivo desta camada e desacoplar quem produz leituras (publisher) de quem
as processa (consumer). Hoje o publisher e o simulador do backend; amanha sera
o agente do Raspberry Pi. Em ambos os casos o backend nao muda: continua a
receber JSON do broker e a reutilizar o pipeline ja existente
(`db.add_sensor_reading` + `process_model_readings`).

Usa um `topic` exchange (em vez de `fanout`) porque da o mesmo comportamento
pub/sub e ainda permite, no futuro, routing por sensor/divisao
(ex.: `sensors.rpi.door`) sem refazer a camada.
"""

from __future__ import annotations

import json

import aio_pika
from aio_pika.abc import AbstractRobustConnection

from ..config import Settings


async def get_connection(settings: Settings) -> AbstractRobustConnection:
    """Abre uma ligacao robusta ao broker.

    `connect_robust` reconecta sozinho se o broker cair/reiniciar, o que e
    essencial para o backend nao crashar quando o RabbitMQ fica indisponivel.
    """
    return await aio_pika.connect_robust(settings.rabbitmq_url)


async def publish_reading(
    channel: aio_pika.abc.AbstractChannel,
    exchange_name: str,
    routing_key: str,
    source: str,
    readings: dict[str, float],
) -> None:
    """Declara o exchange `topic` durable e publica uma leitura como JSON persistente."""
    exchange = await channel.declare_exchange(
        exchange_name,
        aio_pika.ExchangeType.TOPIC,
        durable=True,
    )
    body = json.dumps({"source": source, "readings": readings}).encode("utf-8")
    message = aio_pika.Message(
        body=body,
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await exchange.publish(message, routing_key=routing_key)


async def start_consumer(app, settings: Settings) -> None:
    """Consome leituras do broker e reutiliza o pipeline existente do backend.

    Por cada mensagem (com ack manual apos sucesso):
      1. parse do JSON -> `source`, `readings`;
      2. `app.state.db.add_sensor_reading(readings, source=source)`;
      3. `await process_model_readings(app, readings)`.

    Mantem-se o mesmo padrao de layering ja usado no projeto: o consumer importa
    `process_model_readings` dos routers, tal como o simulador ja fazia.
    """
    # Import local para evitar dependencia circular no arranque do modulo.
    from ..routers.model import process_model_readings

    connection: AbstractRobustConnection = app.state.rabbitmq
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        settings.rabbitmq_exchange,
        aio_pika.ExchangeType.TOPIC,
        durable=True,
    )
    queue = await channel.declare_queue(settings.rabbitmq_queue, durable=True)
    # `sensors.#` apanha tanto `sensors.simulator` como `sensors.rpi` (e futuros).
    await queue.bind(exchange, routing_key="sensors.#")

    print(
        f"Consumer RabbitMQ ligado: exchange='{settings.rabbitmq_exchange}', "
        f"queue='{settings.rabbitmq_queue}', binding='sensors.#'."
    )

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            # `message.process()` faz ack apos o bloco; em caso de excecao
            # a mensagem e devolvida (requeue) e nao se perde.
            async with message.process():
                try:
                    payload = json.loads(message.body.decode("utf-8"))
                except (ValueError, UnicodeDecodeError) as exc:
                    print(f"Aviso: mensagem invalida ignorada: {exc}")
                    continue

                readings = payload.get("readings", {})
                source = payload.get("source", "unknown")
                if not isinstance(readings, dict) or not readings:
                    print("Aviso: mensagem sem 'readings' valido, ignorada.")
                    continue

                app.state.db.add_sensor_reading(readings, source=source)
                try:
                    await process_model_readings(app, readings)
                except Exception as exc:
                    print(f"Aviso: consumer nao conseguiu correr inferencia: {exc}")
