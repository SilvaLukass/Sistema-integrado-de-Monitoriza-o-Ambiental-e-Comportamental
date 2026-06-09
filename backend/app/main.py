import asyncio
import sys
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path

_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telegram import Bot, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
import joblib

from .config import Settings
from .routers.alerts import router as alerts_router
from .routers.camera import router as camera_router
from .routers.devices import router as devices_router
from .routers.model import router as model_router
from .routers.sensors import router as sensors_router
from .routers.system import router as system_router
from .routers.debug import router as debug_router
from .services.alert_store import AlertStore
from .services.camera import CameraCaptureError, capture_frame
from .services.db import init_db
from .services.messaging import get_connection, start_consumer
from .services.simulator import start_simulator
from .services.telegram_notifier import TelegramNotifier


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    app.state.settings = settings
    project_root = Path(__file__).resolve().parents[2]
    app.state.project_root = project_root
    db_path = project_root / settings.sqlite_path
    app.state.db = init_db(db_path)

    app.state.telegram_app = None

    async def handle_camera_callback(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        if query is None:
            return

        if query.data == "cam:no":
            await query.answer("Pedido cancelado.")
            if query.message is not None:
                await query.edit_message_reply_markup(reply_markup=None)
                await query.message.reply_text("Ok, nao sera enviado nenhum frame.")
            return

        if query.data != "cam:yes":
            await query.answer()
            return

        await query.answer("A captar um frame da camara...")
        try:
            frame = await capture_frame(settings)
        except CameraCaptureError as exc:
            if query.message is not None:
                await query.message.reply_text(f"Nao foi possivel obter a imagem: {exc}")
            return

        photo = BytesIO(frame)
        photo.name = "camera-frame.jpg"
        if query.message is not None:
            await query.edit_message_reply_markup(reply_markup=None)
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=photo,
                caption="Frame unico da camara. A imagem nao foi guardada.",
            )

    if settings.telegram_bot_token and settings.telegram_chat_id:
        bot = Bot(token=settings.telegram_bot_token)
        app.state.telegram = TelegramNotifier(bot=bot, chat_id=settings.telegram_chat_id)
        telegram_application = Application.builder().token(
            settings.telegram_bot_token
        ).build()
        telegram_application.add_handler(CallbackQueryHandler(handle_camera_callback))
        await telegram_application.initialize()
        await telegram_application.start()
        if telegram_application.updater is not None:
            await telegram_application.updater.start_polling()
        app.state.telegram_app = telegram_application
    else:
        print("Aviso: Bot do Telegram desativado (Faltam credenciais).")
        app.state.telegram = None

    app.state.alert_store = AlertStore(max_items=500, db=app.state.db)
    app.state.last_low_confidence_alert_at = None
    model_dir = project_root / "App"
    app.state.ml_model = joblib.load(model_dir / "rf_routine_model.pkl")
    app.state.ml_features = joblib.load(model_dir / "rf_features.pkl")
    app.state.ml_label_mapping = joblib.load(model_dir / "rf_label_mapping.pkl")

    app.state.rabbitmq = None
    consumer_task = None
    try:
        app.state.rabbitmq = await get_connection(settings)
        if settings.consumer_enabled:
            consumer_task = asyncio.create_task(start_consumer(app, settings))
    except Exception as exc:
        print(f"Aviso: nao foi possivel ligar ao RabbitMQ: {exc}")

    simulator_task = None
    if settings.simulator_enabled:
        simulator_task = start_simulator(app, settings.simulator_interval_seconds)

    try:
        yield
    finally:
        if simulator_task is not None:
            simulator_task.cancel()
        if consumer_task is not None:
            consumer_task.cancel()
            try:
                await consumer_task
            except (asyncio.CancelledError, Exception):
                pass
        if app.state.rabbitmq is not None:
            await app.state.rabbitmq.close()
        telegram_application = app.state.telegram_app
        if telegram_application is not None:
            if telegram_application.updater is not None:
                await telegram_application.updater.stop()
            await telegram_application.stop()
            await telegram_application.shutdown()
        app.state.db.close()


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
app.include_router(camera_router)
app.include_router(model_router)
app.include_router(sensors_router)
app.include_router(devices_router)
app.include_router(system_router)
app.include_router(debug_router)


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