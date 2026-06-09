const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface RpiMetrics {
  online: boolean
  cpu_percent: number
  memory_percent: number
  temperature_c: number | null
  uptime_seconds: number
}

async function parseJson<T>(res: Response, context: string): Promise<T> {
  if (!res.ok) {
    let detail = ''
    try {
      const body = (await res.json()) as { detail?: string }
      detail = body.detail ? `: ${body.detail}` : ''
    } catch {
      detail = ''
    }
    throw new Error(`${context}: ${res.status}${detail}`)
  }
  return res.json() as Promise<T>
}

async function parseBlob(res: Response, context: string): Promise<Blob> {
  if (!res.ok) {
    let detail = ''
    try {
      const body = (await res.json()) as { detail?: string }
      detail = body.detail ? `: ${body.detail}` : ''
    } catch {
      detail = ''
    }
    throw new Error(`${context}: ${res.status}${detail}`)
  }
  return res.blob()
}

export async function captureCameraFrame(): Promise<Blob> {
  const res = await fetch(`${API_URL}/api/camera/capture`, {
    method: 'POST',
  })
  return parseBlob(res, 'Erro ao pedir imagem da camara')
}

export async function fetchRpiMetrics(): Promise<RpiMetrics> {
  const res = await fetch(`${API_URL}/api/system/rpi-metrics`)
  return parseJson<RpiMetrics>(res, 'Erro ao obter metricas do RPi')
}
