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

export interface LatestSensorsResponse {
  timestamp: string
  readings: Record<string, number>
  co2: number
  co2_status: string
  temperature: number
  last_activity_room: string | null
}

export interface SensorHistoryPoint {
  time: string
  movement: number
  tempHum: number
  co2: number | null
}

export interface DeviceStatus {
  id: string
  name: string
  room: string
  type: string
  online: boolean
  battery: number
  last_seen: string | null
  last_value: string | null
}

export interface ActivityEvent {
  room: string
  time: string
  description: string
  sensorLabel: string
  sensorColor: 'blue' | 'purple'
}

export interface SystemMetrics {
  cpu_usage: number
  memory_usage: number
  temperature: number | null
  uptime_seconds: number
  source: string
  extra: Record<string, unknown>
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

export async function getLatestSensors(): Promise<LatestSensorsResponse> {
  const res = await fetch(`${API_URL}/api/sensors/latest`)
  return parseJson<LatestSensorsResponse>(res, 'Erro ao buscar sensores recentes')
}

export async function getSensorHistory(hours = 24): Promise<SensorHistoryPoint[]> {
  const res = await fetch(`${API_URL}/api/sensors/history?hours=${hours}`)
  return parseJson<SensorHistoryPoint[]>(res, 'Erro ao buscar historico de sensores')
}

export async function getDevices(): Promise<DeviceStatus[]> {
  const res = await fetch(`${API_URL}/api/devices`)
  return parseJson<DeviceStatus[]>(res, 'Erro ao buscar dispositivos')
}

export async function getSystemMetrics(): Promise<SystemMetrics> {
  const res = await fetch(`${API_URL}/api/system/metrics`)
  return parseJson<SystemMetrics>(res, 'Erro ao buscar metricas do sistema')
}

export async function getLatestInference(): Promise<ModelInferenceResponse> {
  const res = await fetch(`${API_URL}/api/model/latest`)
  return parseJson<ModelInferenceResponse>(res, 'Erro ao buscar ultima inferencia')
}

export async function getRecentActivity(): Promise<ActivityEvent[]> {
  const res = await fetch(`${API_URL}/api/activity/recent`)
  return parseJson<ActivityEvent[]>(res, 'Erro ao buscar atividade recente')
}

