from __future__ import annotations

from contextlib import asynccontextmanager
from io import BytesIO

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from telegram import Bot, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from .config import Settings
from .routers.alerts import router as alerts_router
from .routers.camera import router as camera_router
from .routers.system import router as system_router
from .services.camera import CameraCaptureError, capture_frame
from .services.telegram_notifier import TelegramNotifier


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    app.state.settings = settings
    app.state.alerts = []
    app.state.telegram = None
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
        app.state.telegram = TelegramNotifier(
            bot=bot, chat_id=settings.telegram_chat_id
        )
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
        print("Aviso: Bot do Telegram desativado (faltam credenciais).")

    try:
        yield
    finally:
        telegram_application = app.state.telegram_app
        if telegram_application is not None:
            if telegram_application.updater is not None:
                await telegram_application.updater.stop()
            await telegram_application.stop()
            await telegram_application.shutdown()


app = FastAPI(title="ElderCare API", lifespan=lifespan)
settings = Settings()
allowed_origins = [
    origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(camera_router)
app.include_router(system_router)
app.include_router(alerts_router)


@app.get("/health")
async def health():
    return {"ok": True}
