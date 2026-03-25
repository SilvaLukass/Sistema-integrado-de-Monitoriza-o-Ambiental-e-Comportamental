import type { Alert, AlertSeverity } from '../types'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface CreateAlertPayload {
  title: string
  description: string
  severity: AlertSeverity
}

export interface CreateAlertResponse {
  alert: Alert
  notification_sent: boolean
  notification_error: string | null
}

async function parseJson<T>(res: Response, context: string): Promise<T> {
  if (!res.ok) {
    throw new Error(`${context}: ${res.status}`)
  }
  return res.json() as Promise<T>
}

export async function getAlerts(): Promise<Alert[]> {
  const res = await fetch(`${API_URL}/api/alerts`)
  return parseJson<Alert[]>(res, 'Erro ao buscar alertas')
}

export async function createAlert(payload: CreateAlertPayload): Promise<CreateAlertResponse> {
  const res = await fetch(`${API_URL}/api/alerts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return parseJson<CreateAlertResponse>(res, 'Erro ao criar alerta')
}

