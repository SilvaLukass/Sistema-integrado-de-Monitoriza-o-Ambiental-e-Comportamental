export type SensorType = 'pir' | 'door' | 'temperature' | 'humidity' | 'gas' | 'airQuality'

export type SensorStatus = 'online' | 'offline'

export interface SensorReading {
  sensorId: string
  sensorType: SensorType
  room: string
  value: string | number | boolean
  unit?: string
  timestamp: string
}

export interface SensorDevice {
  id: string
  name: string
  type: SensorType
  room: string
  status: SensorStatus
  lastSeen: string
  lastValue?: string | number | boolean
}

export type AlertSeverity = 'warning' | 'success' | 'info' | 'danger'

export interface Alert {
  id: string
  title: string
  description: string
  severity: AlertSeverity
  timestamp: string
  resolved: boolean
}

export interface SystemStatus {
  online: boolean
  lastUpdated: string
  devicesOnline: number
  devicesTotal: number
}