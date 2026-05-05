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

export interface ModelInferencePayload {
  readings: Record<string, number>
}

export interface ModelInferenceResponse {
  expected_activity: string
  confidence: number
  is_anomaly: boolean
  reason: string
  alert_created: boolean
}

export interface OccupancyHeatmapCell {
  day: number
  hour: number
  value: number
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

export async function inferModel(payload: ModelInferencePayload): Promise<ModelInferenceResponse> {
  const res = await fetch(`${API_URL}/api/model/infer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return parseJson<ModelInferenceResponse>(res, 'Erro ao inferir modelo')
}

export async function getOccupancyHeatmap(): Promise<OccupancyHeatmapCell[]> {
  const res = await fetch(`${API_URL}/api/model/occupancy-heatmap`)
  return parseJson<OccupancyHeatmapCell[]>(res, 'Erro ao buscar heatmap')
}

