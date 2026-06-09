from __future__ import annotations
from ..models import Alert, AlertCreate, AlertCreateResult
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Request

from ..services.alert_store import AlertStore
from ..services.telegram_notifier import TelegramNotifier

router = APIRouter()


def _format_ptpt_relative(iso_timestamp: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return iso_timestamp

    now = datetime.now(timezone.utc)
    seconds = int((now - dt.astimezone(timezone.utc)).total_seconds())
    if seconds < 0:
        seconds = 0

    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24

    if minutes < 1:
        return "agora mesmo"
    if minutes < 60:
        return f"há {minutes} minuto" if minutes == 1 else f"há {minutes} minutos"
    if hours < 24:
        return f"há {hours} hora" if hours == 1 else f"há {hours} horas"
    return f"há {days} dia" if days == 1 else f"há {days} dias"


def _severity_prefix(severity: str) -> str:
    return {
        "danger": "ALERTA",
        "warning": "Aviso",
        "info": "Info",
        "success": "OK",
    }.get(severity, "Alerta")


@router.get("/api/alerts", response_model=list[Alert])
async def list_alerts(request: Request):
    store: AlertStore = request.app.state.alert_store
    return store.list()


def create_alert_record(payload: AlertCreate, app) -> Alert:
    alert = Alert(
        id=str(uuid4()),
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        timestamp=Alert.now_iso(),
        resolved=False,
    )

    store: AlertStore = app.state.alert_store
    store.add(alert)
    return alert


def _format_alert_message(alert: Alert, include_camera_prompt: bool = False) -> str:
    relative = _format_ptpt_relative(alert.timestamp)
    text = (
        f"[{_severity_prefix(alert.severity)}] {alert.title}\n"
        f"{alert.description}\n"
        f"({relative})"
    )
    if include_camera_prompt:
        text += "\n\nDeseja receber um frame da camara?"
    return text


async def notify_alert(alert: Alert, app) -> tuple[bool, str | None]:
    notifier: TelegramNotifier | None = app.state.telegram
    if notifier is None:
        return False, "Telegram desativado"

    try:
        if alert.severity == "danger":
            await notifier.send_alert_with_camera_button(
                _format_alert_message(alert, include_camera_prompt=True)
            )
        else:
            await notifier.send_text(_format_alert_message(alert))
        return True, None
    except Exception as exc:
        return False, str(exc)


async def create_and_notify_alert_from_app(payload: AlertCreate, app) -> AlertCreateResult:
    alert = create_alert_record(payload, app)
    sent, error = await notify_alert(alert, app)
    return AlertCreateResult(alert=alert, notification_sent=sent, notification_error=error)


async def create_and_notify_alert(payload: AlertCreate, request: Request) -> AlertCreateResult:
    return await create_and_notify_alert_from_app(payload, request.app)


@router.post("/api/alerts", response_model=AlertCreateResult)
async def create_alert(payload: AlertCreate, request: Request):
    return await create_and_notify_alert(payload, request)
