import { create } from 'zustand'
import type { Alert, SensorDevice, SystemStatus } from '../types'

interface AppState {
  systemStatus: SystemStatus | null
  devices: SensorDevice[]
  alerts: Alert[]
  setSystemStatus: (status: SystemStatus) => void
  setDevices: (devices: SensorDevice[]) => void
  setAlerts: (alerts: Alert[]) => void
  addAlert: (alert: Alert) => void
}

export const useAppStore = create<AppState>((set) => ({
  systemStatus: null,
  devices: [],
  alerts: [],

  setSystemStatus: (status) => set({ systemStatus: status }),

  setDevices: (devices) => set({ devices }),

  setAlerts: (alerts) => set({ alerts }),
  addAlert: (alert) =>
    set((state) => ({ alerts: [alert, ...state.alerts] })),
}))