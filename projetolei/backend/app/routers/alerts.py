from __future__ import annotations

from fastapi import APIRouter, Request

from ..models import Alert, AlertCreate, AlertCreateResult
from ..services.telegram_notifier import TelegramNotifier

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _severity_prefix(severity: str) -> str:
    return {
        "danger": "ALERTA",
        "warning": "Aviso",
        "info": "Info",
        "success": "OK",
    }.get(severity, "Alerta")


def _format_alert_message(alert: Alert, include_camera_prompt: bool = False) -> str:
    text = (
        f"[{_severity_prefix(alert.severity)}] {alert.title}\n"
        f"{alert.description}"
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


@router.get("", response_model=list[Alert])
async def list_alerts(request: Request):
    return request.app.state.alerts


@router.post("", response_model=AlertCreateResult)
async def create_alert(payload: AlertCreate, request: Request):
    alert = Alert.from_create(payload)
    request.app.state.alerts.insert(0, alert)
    sent, error = await notify_alert(alert, request.app)
    return AlertCreateResult(alert=alert, notification_sent=sent, notification_error=error)
