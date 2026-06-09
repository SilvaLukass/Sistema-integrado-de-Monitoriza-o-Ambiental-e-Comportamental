from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    cors_origins: str = "http://localhost:5173"

    # RabbitMQ broker used by the Raspberry Pi sensor publisher.
    rabbitmq_url: str = "amqp://eldercare:eldercare_dev@localhost:5672/"
    rabbitmq_exchange: str = "eldercare.sensors"
    rabbitmq_queue: str = "sensor_readings"
    rabbitmq_routing_key: str = "sensors.rpi"

    # HTTP camera service running on the Raspberry Pi, for example:
    # http://192.168.1.50:5001
    camera_service_url: str = ""
    camera_capture_timeout_seconds: int = 15

    # HTTP metrics service running on the Raspberry Pi, for example:
    # http://192.168.1.50:5002
    metrics_service_url: str = ""
    metrics_fetch_timeout_seconds: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
