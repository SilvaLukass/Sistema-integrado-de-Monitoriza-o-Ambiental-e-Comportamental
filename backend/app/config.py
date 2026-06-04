from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str = "" # Substitua pelo token do seu bot
    telegram_chat_id: str = "" # Substitua pelo ID do chat onde as notificações serão enviadas
    cors_origins: str = "http://localhost:5173"
    simulator_enabled: bool = True
    simulator_interval_seconds: int = 10
    sqlite_path: str = "backend/data/eldercare.sqlite"

    # RabbitMQ (camada de transporte publish/subscribe entre sensores e backend)
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    rabbitmq_exchange: str = "eldercare.sensors"
    rabbitmq_queue: str = "sensor_readings"
    rabbitmq_routing_key: str = "sensors.simulator"  # usado pelo publisher local
    consumer_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")