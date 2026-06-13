from __future__ import annotations

import re
from datetime import datetime, timezone
from html import escape
from uuid import uuid4

from fastapi import APIRouter, Request

from ..models import Alert, AlertCreate, AlertCreateResult

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
        return "Agora mesmo"
    if minutes < 60:
        return f"Há {minutes} minuto" if minutes == 1 else f"Há {minutes} minutos"
    if hours < 24:
        return f"Há {hours} hora" if hours == 1 else f"Há {hours} horas"
    return f"Há {days} dia" if days == 1 else f"Há {days} dias"


def _severity_prefix(severity: str) -> str:
    return {
        "danger": "ALERTA",
        "warning": "Aviso",
        "info": "Info",
        "success": "OK",
    }.get(severity, "Alerta")


def _severity_emoji(severity: str) -> str:
    return {
        "danger": "🚨",
        "warning": "⚠️",
        "info": "ℹ️",
        "success": "✅",
    }.get(severity, "📢")


def _prettify_numbers(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        raw = match.group(0)
        value = float(raw)
        if abs(value - round(value)) < 1e-6:
            return f"{int(round(value)):,}".replace(",", " ")
        formatted = f"{value:.1f}".rstrip("0").rstrip(".")
        return formatted

    return re.sub(r"\d+(?:\.\d+)?", replace, text)


def _telegram_title(alert: Alert) -> str:
    title = alert.title.strip()
    for prefix in ("Alerta imediato:", "Alerta imediato :"):
        if title.lower().startswith(prefix.lower()):
            return title[len(prefix) :].strip()
    return title


def _telegram_body(alert: Alert, title: str) -> str:
    description = alert.description.strip()
    boilerplate_prefix = "Valor anormal detetado no sensor. Motivo:"
    if description.lower().startswith(boilerplate_prefix.lower()):
        reason = description[len(boilerplate_prefix) :].strip().rstrip(".")
        if reason == title or reason in title or title in reason:
            return ""

    if description and description != title:
        return description
    return ""


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
    raw_title = _telegram_title(alert)
    title = escape(_prettify_numbers(raw_title))
    body = escape(_prettify_numbers(_telegram_body(alert, raw_title)))
    severity_label = escape(_severity_prefix(alert.severity))

    lines = [
        f"{_severity_emoji(alert.severity)} <b>ElderCare — {severity_label}</b>",
        "",
        f"<b>{title}</b>",
    ]
    if body:
        lines.extend(["", body])
    lines.extend(["", f"<i>{escape(relative)}</i>"])
    if include_camera_prompt:
        lines.extend(["", "Deseja receber um frame da câmara?"])
    return "\n".join(lines)


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
