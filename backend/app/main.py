from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telegram import Bot
from collections import deque
from pathlib import Path
import joblib

from .config import Settings
from .routers.alerts import router as alerts_router
from .routers.model import router as model_router
from .services.alert_store import AlertStore
from .services.telegram_notifier import TelegramNotifier


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    if settings.telegram_bot_token and settings.telegram_chat_id:
        bot = Bot(token=settings.telegram_bot_token)
        app.state.telegram = TelegramNotifier(bot=bot, chat_id=settings.telegram_chat_id)
    else:
        print("Aviso: Bot do Telegram desativado (Faltam credenciais).")
        app.state.telegram = None # Para não quebrar o resto do código

    app.state.alert_store = AlertStore(max_items=500)
    app.state.model_inference_store = deque(maxlen=2000)
    app.state.last_low_confidence_alert_at = None
    project_root = Path(__file__).resolve().parents[2]
    model_dir = project_root / "App"
    app.state.ml_model = joblib.load(model_dir / "rf_routine_model.pkl")
    app.state.ml_features = joblib.load(model_dir / "rf_features.pkl")
    app.state.ml_label_mapping = joblib.load(model_dir / "rf_label_mapping.pkl")
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
app.include_router(model_router)


@app.get("/health")
async def health():
    return {"ok": True}


class TestNotificationRequest(BaseModel):
    text: str = "ElderCare: Notificação de teste"


@app.post("/api/notifications/test")
#request : Request dá acesso à instância da aplicação (request.app)
async def test_notification(payload: TestNotificationRequest, request: Request):
    notifier = request.app.state.telegram
    if not notifier:
        return {"sent": False, "error": "Telegram desativado"}
    await notifier.send_text(payload.text)
    return {"sent": True}