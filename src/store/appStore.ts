import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Alert, SensorDevice, SystemStatus } from '../types'

interface AppState {
  systemStatus: SystemStatus | null
  devices: SensorDevice[]
  alerts: Alert[]
  simpleMode: boolean
  setSystemStatus: (status: SystemStatus) => void
  setDevices: (devices: SensorDevice[]) => void
  setAlerts: (alerts: Alert[]) => void
  addAlert: (alert: Alert) => void
  toggleSimpleMode: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      systemStatus: null,
      devices: [],
      alerts: [],
      simpleMode: false,
      setSystemStatus: (status) => set({ systemStatus: status }),

      setDevices: (devices) => set({ devices }),

      setAlerts: (alerts) => set({ alerts }),
      addAlert: (alert) =>
        set((state) => ({ alerts: [alert, ...state.alerts] })),
      toggleSimpleMode: () => set((state) => ({ simpleMode: !state.simpleMode })),
    }),
    {
      name: 'eldercare-ui-preferences',
      partialize: (state) => ({ simpleMode: state.simpleMode }),
    },
  ),
)