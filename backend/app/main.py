from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telegram import Bot

from .config import Settings
from .routers.alerts import router as alerts_router
from .services.alert_store import AlertStore
from .services.telegram_notifier import TelegramNotifier


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    bot = Bot(token=settings.telegram_bot_token)
    app.state.telegram = TelegramNotifier(bot=bot, chat_id=settings.telegram_chat_id)
    app.state.alert_store = AlertStore(max_items=500)
    yield


app = FastAPI(title="ElderCare API", lifespan=lifespan)
settings = Settings()
allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(alerts_router)


@app.get("/health")
async def health():
    return {"ok": True}


class TestNotificationRequest(BaseModel):
    text: str = "ElderCare: Notificação de teste"


@app.post("/api/notifications/test")
#request : Request dá acesso à instância da aplicação (request.app)
async def test_notification(payload: TestNotificationRequest, request: Request):
    notifier: TelegramNotifier = request.app.state.telegram
    await notifier.send_text(payload.text)
    return {"sent": True}