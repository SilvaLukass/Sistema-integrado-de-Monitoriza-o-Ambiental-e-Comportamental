# ElderCare Raspberry Pi agent

This folder is the code that runs on the Raspberry Pi. It reads the local
sensors and publishes the same JSON contract already consumed by the backend:

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

The message is published to the durable RabbitMQ topic exchange
`eldercare.sensors` with routing key `sensors.rpi`.

## Install on the Raspberry Pi

```bash
cd projetolei
python3 -m venv .venv-rpi
source .venv-rpi/bin/activate
pip install -r rpi_agent/requirements.txt
```

## Sensor wiring defaults

- Magnetic door sensor: board `D23` / BCM GPIO 23 (`--door-pin 23`)
- PIR movement sensor: BCM GPIO 17 (`--pir-pin 17`)
- AM2320 temperature/humidity sensor: I2C (`SDA`/`SCL`)

If your reed switch reports the inverse state, run the agent with
`--door-active-low`.

## Run with mock readings

Use this before connecting GPIO hardware:

```bash
python -m rpi_agent.main \
  --mock \
  --broker-url amqp://eldercare:PASSWORD@BROKER_IP:5672/
```

Expected result: `GET /api/sensors/latest` and `GET /api/devices` on the
backend show `D001`, `T001`, and `H001` as recent readings once the backend
consumer is running.

## Run with real sensors

```bash
python -m rpi_agent.main \
  --broker-url amqp://eldercare:PASSWORD@BROKER_IP:5672/ \
  --door-pin 23 \
  --pir-pin 17
```

The agent publishes every 10 seconds by default and also publishes immediately
when the door state changes.

## Camera service

Install `fswebcam` on the RPi:

```bash
sudo apt update
sudo apt install fswebcam
```

Run the camera service:

```bash
python rpi_agent/camera_service.py
```

The backend should use:

```env
CAMERA_SERVICE_URL=http://RPI_IP:5001
```

The service captures one JPEG only when `/capture` is called. The platform
streams the bytes back to the requester and does not store the frame.

## systemd unit: sensor agent

Create `/etc/systemd/system/eldercare-rpi-agent.service`:

```ini
[Unit]
Description=ElderCare Raspberry Pi sensor agent
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/home/pi/projetolei
ExecStart=/home/pi/projetolei/.venv-rpi/bin/python -m rpi_agent.main --broker-url amqp://eldercare:PASSWORD@BROKER_IP:5672/
Restart=always
RestartSec=5
User=pi

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now eldercare-rpi-agent
```

## systemd unit: camera service

Create `/etc/systemd/system/eldercare-camera.service`:

```ini
[Unit]
Description=ElderCare on-demand camera service
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/home/pi/projetolei
ExecStart=/home/pi/projetolei/.venv-rpi/bin/python rpi_agent/camera_service.py
Restart=always
RestartSec=5
User=pi

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now eldercare-camera
```
