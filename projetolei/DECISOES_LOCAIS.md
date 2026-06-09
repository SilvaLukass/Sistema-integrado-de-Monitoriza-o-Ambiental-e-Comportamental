# Decisoes locais - RPi sensors and on-demand camera

## RabbitMQ broker and credentials

- The Raspberry Pi publishes sensor readings to RabbitMQ with routing key
  `sensors.rpi`.
- The backend consumes the same message shape already planned for the simulator:

```json
{
  "source": "rpi",
  "readings": {
    "hour": 14,
    "day_of_week": 3,
    "minute": 5,
    "D001": 0,
    "T001": 22.4,
    "H001": 48.0
  }
}
```

- Do not use RabbitMQ's `guest` account from the RPi. It is intended for
  localhost access only.
- `docker-compose.yml` now starts RabbitMQ with a dedicated LAN-capable user:
  `eldercare`.
- Development URL:

```env
RABBITMQ_URL=amqp://eldercare:eldercare_dev@BROKER_IP:5672/
```

Replace `BROKER_IP` with the IP of the machine running RabbitMQ. For a real
deployment, change `eldercare_dev` to a stronger password in both
`docker-compose.yml` and the RPi/backend environment.

## Sensor mapping

- Reed switch / magnetic door sensor -> `D001`
  - `0`: closed
  - `1`: open
- DHT22 temperature -> `T001` in Celsius
- DHT22 humidity -> `H001` as percentage

The RPi agent intentionally does not need the dashboard, ML model, or database.
It only publishes readings to RabbitMQ. The backend remains responsible for
persistence, inference, alerts, and UI APIs.

## On-demand camera

- Telemetry uses RabbitMQ because it is asynchronous sensor data.
- Camera capture uses HTTP request/reply because it is user-triggered and needs
  one immediate JPEG response.
- The PlayStation camera is served by `rpi_agent/camera_service.py` on the RPi.
- Backend setting:

```env
CAMERA_SERVICE_URL=http://RPI_IP:5001
```

- Privacy rule: the platform requests exactly one frame and streams/sends the
  JPEG bytes without storing the image. The RPi service writes only the
  temporary `/tmp/foto_atual.jpg` capture used by `fswebcam`.

## Telegram interaction

Danger alerts include the prompt:

```text
Deseja receber um frame da camara?
```

The `Sim` callback captures one frame through the backend's shared camera helper
and sends it as a Telegram photo. The `Nao` callback acknowledges the request
without contacting the camera service.
