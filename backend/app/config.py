from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str = "" # Substitua pelo token do seu bot
    telegram_chat_id: str = "" # Substitua pelo ID do chat onde as notificações serão enviadas
    cors_origins: str = "http://localhost:5173"
    simulator_enabled: bool = True
    simulator_interval_seconds: int = 10
    sqlite_path: str = "backend/data/eldercare.sqlite"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")