"""Teste de latencia de publicacao AMQP (RPi -> broker RabbitMQ).

Corre no Raspberry Pi. Mede o tempo de ida-e-volta entre publicar uma mensagem
e o broker confirmar a sua rececao (publisher confirms). Esta latencia
corresponde a perna de comunicacao RPi -> broker e NAO depende de sincronizacao
de relogios entre maquinas, pelo que e um numero fiavel e auto-contido.

A latencia ponta-a-ponta (publish -> consumo no backend) e observavel nos logs
do backend, atraves do campo `published_at` que o publisher passou a incluir em
cada mensagem. Essa medicao requer relogios sincronizados por NTP entre o RPi e
o servidor.

Por defeito, a routing key (`latency.probe`) fica FORA do binding `sensors.#`
do backend, pelo que estas mensagens de teste NAO sao consumidas nem poluem a
base de dados. Para exercitar o pipeline completo (publish -> consumo -> modelo
-> BD) use `--routing-key sensors.rpi`.

Exemplo:
    python -m rpi_agent.latency_test \\
        --broker-url amqp://eldercare:PASSWORD@BROKER_IP:5672/ \\
        --count 100 --interval 0.5
"""

from __future__ import annotations

import argparse
import json
import statistics
import time

import pika


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mede a latencia de publicacao AMQP do RPi ao broker RabbitMQ"
    )
    parser.add_argument(
        "--broker-url",
        required=True,
        help="RabbitMQ URL, e.g. amqp://eldercare:password@192.168.1.10:5672/",
    )
    parser.add_argument("--exchange", default="eldercare.sensors")
    parser.add_argument(
        "--routing-key",
        default="latency.probe",
        help=(
            "Default fora de 'sensors.#' para nao poluir a BD. "
            "Use 'sensors.rpi' para exercitar o pipeline completo."
        ),
    )
    parser.add_argument("--count", type=int, default=100, help="Numero de mensagens a publicar")
    parser.add_argument("--interval", type=float, default=0.5, help="Segundos entre publicacoes")
    parser.add_argument("--source", default="latency_test")
    return parser.parse_args()


def percentile(samples: list[float], pct: float) -> float:
    if not samples:
        return float("nan")
    ordered = sorted(samples)
    index = int(round((pct / 100.0) * (len(ordered) - 1)))
    index = max(0, min(len(ordered) - 1, index))
    return ordered[index]


def main() -> None:
    args = parse_args()

    parameters = pika.URLParameters(args.broker_url)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare(
        exchange=args.exchange,
        exchange_type="topic",
        durable=True,
    )
    # Publisher confirms: basic_publish bloqueia ate o broker confirmar a rececao.
    channel.confirm_delivery()

    properties = pika.BasicProperties(
        content_type="application/json",
        delivery_mode=2,
    )

    samples_ms: list[float] = []
    print(
        f"A publicar {args.count} mensagens para exchange='{args.exchange}', "
        f"routing_key='{args.routing_key}'..."
    )

    for seq in range(1, args.count + 1):
        body = json.dumps(
            {
                "source": args.source,
                "readings": {"latency_probe": 1},
                "published_at": time.time(),
                "seq": seq,
            }
        ).encode("utf-8")

        start = time.perf_counter()
        try:
            channel.basic_publish(
                exchange=args.exchange,
                routing_key=args.routing_key,
                body=body,
                properties=properties,
            )
        except Exception as exc:  # noqa: BLE001 - reportar e continuar
            print(f"  msg {seq}: FALHA na publicacao: {exc}")
            continue

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        samples_ms.append(elapsed_ms)

        if args.interval > 0:
            time.sleep(args.interval)

    connection.close()

    if not samples_ms:
        print("Sem amostras validas. Verifique a ligacao ao broker.")
        return

    print("\n=== Latencia de publicacao RPi -> broker (publisher confirm) ===")
    print(f"  Amostras : {len(samples_ms)}")
    print(f"  Minimo   : {min(samples_ms):.2f} ms")
    print(f"  Media    : {statistics.mean(samples_ms):.2f} ms")
    print(f"  Mediana  : {statistics.median(samples_ms):.2f} ms")
    print(f"  p95      : {percentile(samples_ms, 95):.2f} ms")
    print(f"  Maximo   : {max(samples_ms):.2f} ms")


if __name__ == "__main__":
    main()
