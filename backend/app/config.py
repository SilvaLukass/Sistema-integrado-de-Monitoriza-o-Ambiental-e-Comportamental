from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str = "" # Substitua pelo token do seu bot
    telegram_chat_id: str = "" # Substitua pelo ID do chat onde as notificações serão enviadas
    cors_origins: str = "http://localhost:5173"
    simulator_enabled: bool = False
    simulator_interval_seconds: int = 10
    sqlite_path: str = "backend/data/eldercare.sqlite"

    camera_service_url: str = ""
    camera_capture_timeout_seconds: int = 15

    # HTTP metrics service running on the Raspberry Pi, for example:
    # http://192.168.1.50:5002
    metrics_service_url: str = ""
    metrics_fetch_timeout_seconds: int = 5

    # RabbitMQ (camada de transporte publish/subscribe entre sensores e backend)
    rabbitmq_url: str = "amqp://eldercare:eldercare_dev@localhost:5672/"
    rabbitmq_exchange: str = "eldercare.sensors"
    rabbitmq_queue: str = "sensor_readings"
    rabbitmq_routing_key: str = "sensors.simulator"  # usado pelo publisher local
    consumer_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")