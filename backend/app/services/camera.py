from __future__ import annotations

from urllib.parse import urljoin

import httpx

from ..config import Settings


class CameraCaptureError(RuntimeError):
    """Raised when the Raspberry Pi camera service cannot provide a frame."""


async def capture_frame(settings: Settings) -> bytes:
    """Capture a single frame from the RPi camera service.

    The image stays in memory only; callers stream or send the bytes directly.
    """
    base_url = settings.camera_service_url.strip()
    if not base_url:
        raise CameraCaptureError("CAMERA_SERVICE_URL nao configurado.")

    capture_url = urljoin(base_url.rstrip("/") + "/", "capture")
    timeout = httpx.Timeout(float(settings.camera_capture_timeout_seconds))

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(capture_url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise CameraCaptureError(f"Falha ao contactar a camara no RPi: {exc}") from exc

    content_type = response.headers.get("content-type", "")
    if "image/jpeg" not in content_type.lower():
        raise CameraCaptureError(
            f"Resposta inesperada da camara: content-type '{content_type or 'desconhecido'}'."
        )

    if not response.content:
        raise CameraCaptureError("A camara devolveu uma imagem vazia.")

    return response.content
