from __future__ import annotations

from urllib.parse import urljoin

import httpx

from ..config import Settings


class RpiMetricsError(RuntimeError):
    """Raised when the Raspberry Pi metrics service cannot be reached."""


async def fetch_rpi_metrics(settings: Settings) -> dict[str, float | int | None]:
    """Fetch host metrics from the HTTP service running on the Raspberry Pi."""
    base_url = settings.metrics_service_url.strip()
    if not base_url:
        raise RpiMetricsError("METRICS_SERVICE_URL nao configurado.")

    metrics_url = urljoin(base_url.rstrip("/") + "/", "metrics")
    timeout = httpx.Timeout(float(settings.metrics_fetch_timeout_seconds))

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(metrics_url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RpiMetricsError(f"Falha ao contactar o RPi: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise RpiMetricsError("Resposta de metricas invalida do RPi.") from exc

    required_fields = ("cpu_percent", "memory_percent", "uptime_seconds")
    for field in required_fields:
        if field not in payload:
            raise RpiMetricsError(f"Resposta de metricas incompleta: falta '{field}'.")

    return payload
