import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Activity, AlertTriangle, Bell, Cpu, Flame, Leaf, ShieldCheck, Wifi } from 'lucide-react'
import type { AlertSeverity } from '../types'
import {
  getAlerts,
  getDevices,
  getLatestInference,
  getLatestSensors,
  getRecentActivity,
  inferModel,
  type ActivityEvent,
  type DeviceStatus,
} from '../api/backend'
import { useAppStore } from '../store/appStore'
import { useSimulator } from '../hooks/useSimulator'

function CardHeader({ icon, title, subtitle, iconBg }: {
  icon: React.ReactNode
  title: string
  subtitle: string
  iconBg: string
}) {
  return (
    <div className="flex items-center gap-3">
      <div className={`size-10 ${iconBg} rounded-[14px] flex items-center justify-center shrink-0`}>
        {icon}
      </div>
      <div>
        <p className="font-semibold text-lg text-[#101828]">{title}</p>
        <p className="text-sm text-[#6a7282]">{subtitle}</p>
      </div>
    </div>
  )
}

function SafetyStatusHeader() {
  const { t } = useTranslation()
  const { data: aiStatus, isError } = useQuery({
    queryKey: ['model-latest'],
    queryFn: getLatestInference,
    refetchInterval: 1000,
    retry: false,
  })
  const { data: sensors } = useQuery({
    queryKey: ['latest-sensors'],
    queryFn: getLatestSensors,
    refetchInterval: 1000,
    retry: false,
  })

  const co2 = sensors?.co2 ?? 0
  const isRoutineAnomaly = aiStatus?.is_anomaly ?? false
  const isAirQualityDanger = co2 > 1200
  const isDanger = isRoutineAnomaly || isAirQualityDanger

  const bgColor = isDanger ? 'bg-[#fff1f2]' : 'bg-[#f0fdf4]'
  const borderColor = isDanger ? 'border-[#ef4444]' : 'border-[#10b981]'
  const textColor = isDanger ? 'text-[#ef4444]' : 'text-[#10b981]'
  const Icon = isDanger ? AlertTriangle : ShieldCheck

  return (
    <div className={`bg-white border rounded-[14px] shadow-sm px-6 py-6 transition-colors duration-500 ${isDanger ? 'border-[#ef4444]' : 'border-[#e5e7eb]'}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`size-16 ${bgColor} rounded-[14px] flex items-center justify-center`}>
            {isAirQualityDanger && !isRoutineAnomaly ? (
              <Flame size={32} className={textColor} />
            ) : (
              <Icon size={32} className={textColor} />
            )}
          </div>
          <div>
            <p className="font-semibold text-2xl text-[#101828]">
              {isAirQualityDanger ? 'Alerta: Qualidade do Ar Perigosa!' :
                isRoutineAnomaly ? 'Anomalia Detetada na Rotina!' :
                  t('overview.safetyTitle')}
            </p>

            <p className="text-sm text-[#6a7282] mt-1">
              {isError ? 'A aguardar primeira inferência da Inteligência Artificial...' :
                aiStatus ? (
                  <>
                    {isAirQualityDanger && (
                      <span className="font-bold text-red-600 block mb-1">
                        Níveis de CO2 atuais: {co2} ppm
                      </span>
                    )}
                    A prever <strong>{t(`activities.${aiStatus.expected_activity}`, { defaultValue: aiStatus.expected_activity })}</strong>
                    <br />
                    <span className="text-xs italic text-gray-500">
                      Baseado {aiStatus.reason || 'nos padrões recentes.'} Confiança: {aiStatus.confidence.toFixed(1)}%
                    </span>
                  </>
                ) : 'A analisar sensores...'}
            </p>
          </div>
        </div>
        {aiStatus && (
          <div className={`border-2 ${borderColor} ${bgColor} rounded-[14px] px-6 py-3 text-center`}>
            <p className={`font-semibold text-lg ${textColor}`}>
              {isDanger ? 'Requer Atenção' : t('overview.allClear')}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

function formatActivityTime(timestamp: string) {
  return new Date(timestamp).toLocaleString('pt-PT', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

function ResidentActivityCard() {
  const { t } = useTranslation()
  const { data: activity = [] } = useQuery({
    queryKey: ['activity-recent'],
    queryFn: getRecentActivity,
    refetchInterval: 1000,
  })

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <CardHeader
        icon={<Activity size={20} className="text-[#2563eb]" />}
        title={t('overview.residentActivity')}
        subtitle={t('overview.recentMovements')}
        iconBg="bg-[#eff6ff]"
      />

      <div className="flex flex-col gap-4">
        {activity.length === 0 && (
          <div className="border border-dashed border-[#d0d5dd] rounded-[14px] px-4 py-5 text-sm text-[#6a7282]">
            Sem movimentos recentes.
          </div>
        )}
        {activity.map((event: ActivityEvent, index) => (
          <div key={`${event.timestamp}-${event.room}-${index}`} className="flex gap-4">
            <div className="flex flex-col items-center w-3 shrink-0">
              <div className="size-3 rounded-full bg-[#2563eb] shrink-0" />
              {index < activity.length - 1 && (
                <div className="w-0.5 flex-1 bg-[#e5e7eb] mt-1" />
              )}
            </div>

            <div className="pb-4 flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="font-medium text-base text-[#101828]">{event.room}</p>
                <p className="text-sm text-[#6a7282]">{formatActivityTime(event.timestamp)}</p>
              </div>
              <p className="text-sm text-[#4a5565] mt-1">{event.description}</p>
              <span className={`inline-block mt-2 px-3 py-1 rounded-[10px] text-xs font-medium ${
                event.sensorColor === 'blue'
                  ? 'bg-[#eff6ff] text-[#2563eb]'
                  : 'bg-[#faf5ff] text-[#9810fa]'
              }`}>
                {event.sensorLabel}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function metricPercentage(value: number, max: number) {
  return Math.max(0, Math.min((value / max) * 100, 100))
}

function co2Status(co2: number): 'good' | 'warning' | 'danger' {
  if (co2 <= 800) return 'good'
  if (co2 <= 1200) return 'warning'
  return 'danger'
}

function EnvironmentalHealthCard() {
  const { t } = useTranslation()
  const { data } = useQuery({
    queryKey: ['latest-sensors'],
    queryFn: getLatestSensors,
  })

  const statusColors = {
    good: { bar: 'bg-[#10b981]', badge: 'bg-[rgba(16,185,129,0.13)] text-[#10b981]', label: t('status.good') },
    warning: { bar: 'bg-[#f59e0b]', badge: 'bg-[#fffbeb] text-[#f59e0b]', label: t('status.warning') },
    danger: { bar: 'bg-[#ef4444]', badge: 'bg-[#fff1f2] text-[#ef4444]', label: t('status.danger') },
  }

  const metrics = data
    ? [
        {
          label: t('sensors.co2'),
          value: String(Math.round(data.co2)),
          unit: 'ppm',
          min: '0 ppm',
          max: '1600 ppm',
          status: co2Status(data.co2),
          percentage: metricPercentage(data.co2, 1600),
        },
        {
          label: t('sensors.temperature'),
          value: data.temperature.toFixed(1),
          unit: '°C',
          min: '10°C',
          max: '40°C',
          status: 'good' as const,
          percentage: metricPercentage(data.temperature - 10, 30),
        },
      ]
    : []

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <CardHeader
        icon={<Leaf size={20} className="text-[#10b981]" />}
        title={t('overview.environmentalHealth')}
        subtitle={t('overview.airQualityTemp')}
        iconBg="bg-[#f0fdf4]"
      />

      <div className="flex flex-col gap-6">
        {metrics.length === 0 && (
          <div className="border border-dashed border-[#d0d5dd] rounded-[14px] px-4 py-5 text-sm text-[#6a7282]">
            A aguardar leituras ambientais.
          </div>
        )}
        {metrics.map((metric) => {
          const colors = statusColors[metric.status]
          return (
            <div key={metric.label}>
              <div className="flex items-center justify-between mb-3">
                <p className="font-medium text-base text-[#101828]">{metric.label}</p>
                <p className="font-semibold text-2xl text-[#101828]">
                  {metric.value}<span className="text-base ml-1">{metric.unit}</span>
                </p>
              </div>

              <div className="h-3 bg-[#f3f4f6] rounded-full overflow-hidden">
                <div
                  className={`h-full ${colors.bar} rounded-full transition-all duration-500`}
                  style={{ width: `${metric.percentage}%` }}
                />
              </div>

              <div className="flex items-center justify-between mt-2">
                <p className="text-xs text-[#6a7282]">{metric.min}</p>
                <span className={`px-3 py-1 rounded-[10px] text-sm font-medium ${colors.badge}`}>
                  {colors.label}
                </span>
                <p className="text-xs text-[#6a7282]">{metric.max}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function RecentAlertsCard() {
  const { t } = useTranslation()

  const severityStyles: Record<AlertSeverity, string> = {
    warning: 'bg-[#fffbeb] border-[#fee685]',
    success: 'bg-[#f0fdf4] border-[#b9f8cf]',
    info: 'bg-[#eff6ff] border-[#bedbff]',
    danger: 'bg-[#fff1f2] border-[#fecdd3]',
  }

  const { data: alerts = [] } = useQuery({
    queryKey: ['alerts'],
    queryFn: getAlerts,
    refetchInterval: 10_000,
  })
  const renderedAlerts = alerts.slice(0, 3)

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <CardHeader
        icon={<Bell size={20} className="text-[#f59e0b]" />}
        title={t('overview.recentAlerts')}
        subtitle={t('overview.last24h')}
        iconBg="bg-[#fffbeb]"
      />

      <div className="flex flex-col gap-3">
        {renderedAlerts.length === 0 && (
          <div className="border border-dashed border-[#d0d5dd] rounded-[14px] px-4 py-5 text-sm text-[#6a7282]">
            Sem alertas recentes.
          </div>
        )}
        {renderedAlerts.map((alert) => (
          <div key={alert.id} className={`${severityStyles[alert.severity]} border rounded-[14px] px-4 py-4`}>
            <div className="flex items-start justify-between gap-2">
              <p className="font-semibold text-base text-[#101828]">{alert.title}</p>
              <p className="text-xs text-[#6a7282] shrink-0">
                {new Date(alert.timestamp).toLocaleString('pt-PT', { dateStyle: 'short', timeStyle: 'short' })}
              </p>
            </div>
            <p className="text-sm text-[#4a5565] mt-1">{alert.description}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function formatLastSeen(lastSeen: string | null) {
  if (!lastSeen) return 'sem dados'
  const diffMs = Date.now() - new Date(lastSeen).getTime()
  const minutes = Math.max(0, Math.round(diffMs / 60_000))
  if (minutes < 1) return 'agora mesmo'
  return `há ${minutes} min`
}

function DeviceStatusCard() {
  const { t } = useTranslation()
  const simpleMode = useAppStore((state) => state.simpleMode)
  const { data: devices = [] } = useQuery({
    queryKey: ['devices'],
    queryFn: getDevices,
    refetchInterval: 5_000,
  })
  const visibleDevices = devices
  const onlineCount = devices.filter((device: DeviceStatus) => device.online).length

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <CardHeader
        icon={<Cpu size={20} className="text-[#2563eb]" />}
        title={t('overview.deviceStatus')}
        subtitle={t('overview.devicesOnline', { online: onlineCount, total: devices.length })}
        iconBg="bg-[#eff6ff]"
      />

      <div className="flex flex-col gap-3">
        {visibleDevices.length === 0 && (
          <div className="border border-dashed border-[#d0d5dd] rounded-[14px] px-4 py-5 text-sm text-[#6a7282]">
            A aguardar dispositivos.
          </div>
        )}
        {visibleDevices.map((device: DeviceStatus) => (
          <div key={device.id} className="border border-[#e5e7eb] rounded-[14px] px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Wifi size={20} className={device.online ? 'text-[#2563eb] shrink-0' : 'text-[#9ca3af] shrink-0'} />
                <div>
                  <p className="font-semibold text-base text-[#101828]">{device.name}</p>
                  {!simpleMode && <p className="text-sm text-[#6a7282]">{device.room}</p>}
                </div>
              </div>
              <span className={`text-xs font-medium px-2 py-1 rounded-[10px] ${
                device.online ? 'bg-[#f0fdf4] text-[#10b981]' : 'bg-[#f3f4f6] text-[#6a7282]'
              }`}>
                {device.online ? t('status.online') : t('status.offline')}
              </span>
            </div>

            {!simpleMode && (
              <div className="flex items-center justify-end mt-3">
                <p className="text-xs text-[#6a7282]">{t('common.lastSeenTime', { time: formatLastSeen(device.last_seen) })}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export function DebugModeButton() {
  const queryClient = useQueryClient()
  const [manualOpen, setManualOpen] = useState(false)
  const [simOpen, setSimOpen] = useState(false)
  const [horaInicio, setHoraInicio] = useState<number | undefined>(undefined)
  const [isSending, setIsSending] = useState(false)
  const [horaManual, setHoraManual] = useState<number>(14)
  const [m003Manual, setM003Manual] = useState<number>(1)
  const [co2Manual, setCo2Manual] = useState<number>(500)
  const [m004Manual, setM004Manual] = useState<number>(0)
  const [m018Manual, setM018Manual] = useState<number>(0)
  const [m001Manual, setM001Manual] = useState<number>(0)
  const [d001Manual, setD001Manual] = useState<number>(0)
  const [t001Manual, setT001Manual] = useState<number>(22.5)
  const { eventos, ativo } = useSimulator(simOpen, horaInicio)

  async function submitDebugReading() {
    setIsSending(true)
    const jsDay = new Date().getDay()
    const pandasDayOfWeek = (jsDay + 6) % 7
    await inferModel({
      readings: {
        hour: horaManual,
        day_of_week: pandasDayOfWeek,
        minute: 0,
        M001: m001Manual,
        M003: m003Manual,
        M004: m004Manual,
        M018: m018Manual,
        D001: d001Manual,
        T001: t001Manual,
        CO2: co2Manual,
      },
    })
    await queryClient.invalidateQueries()
    setIsSending(false)
  }

  return (
    <>
      <div className="flex flex-wrap items-center gap-3 p-4">
        <button
          onClick={() => setManualOpen(!manualOpen)}
          className="bg-gray-800 text-white px-4 py-2 rounded-[14px] text-sm font-medium hover:bg-gray-700 transition-colors"
        >
          {manualOpen ? 'Fechar teste manual' : 'Teste manual IA'}
        </button>
        <button
          onClick={() => setSimOpen(true)}
          className="bg-gray-800 text-white px-4 py-2 rounded-[14px] text-sm font-medium hover:bg-gray-700 transition-colors"
        >
          Simulador Aruba (SSE)
        </button>
        <select
          value={horaInicio ?? ''}
          onChange={(e) => setHoraInicio(e.target.value ? Number(e.target.value) : undefined)}
          className="border border-[#e5e7eb] rounded-[10px] px-3 py-2 text-sm text-[#101828]"
        >
          <option value="">Início do dataset</option>
          {Array.from({ length: 24 }, (_, i) => (
            <option key={i} value={i}>{String(i).padStart(2, '0')}:00h</option>
          ))}
        </select>
      </div>

      {manualOpen && (
        <div className="mx-4 mb-4 bg-[#f8fafc] border border-gray-200 rounded-[14px] p-6 shadow-sm">
          <p className="font-semibold text-[#101828] mb-1">Painel de Controlo Manual (Testes IA)</p>
          <p className="text-sm text-[#6a7282] mb-4">
            Chama o endpoint de inferência com valores escolhidos. O fluxo principal usa dados persistidos pelo backend.
          </p>
          <div className="grid grid-cols-2 gap-4">
            {[
              ['Hora do Dia', horaManual, setHoraManual],
              ['Sensor M001 (Sala)', m001Manual, setM001Manual],
              ['Sensor M003 (Cama)', m003Manual, setM003Manual],
              ['Sensor M004 (Casa de Banho)', m004Manual, setM004Manual],
              ['Sensor M018 (Cozinha)', m018Manual, setM018Manual],
              ['Sensor D001 (Porta Principal)', d001Manual, setD001Manual],
              ['Sensor T001 (Temperatura)', t001Manual, setT001Manual],
              ['Sensor CO2', co2Manual, setCo2Manual],
            ].map(([label, value, setter]) => (
              <div key={label as string}>
                <label className="block text-sm text-gray-600 mb-1">{label as string}</label>
                <input
                  type="number"
                  value={value as number}
                  onChange={(event) => (setter as React.Dispatch<React.SetStateAction<number>>)(Number(event.target.value))}
                  className="border p-2 rounded-[10px] w-full"
                />
              </div>
            ))}
          </div>
          <button
            onClick={submitDebugReading}
            disabled={isSending}
            className="mt-4 bg-[#2563eb] text-white px-4 py-2 rounded-[14px] text-sm font-medium disabled:opacity-60"
          >
            {isSending ? 'A testar...' : 'Testar leitura na IA'}
          </button>
        </div>
      )}

      {simOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setSimOpen(false)}
          />
          <div className="relative w-[600px] h-full bg-white shadow-xl flex flex-col overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#e5e7eb]">
              <div>
                <p className="font-semibold text-lg text-[#101828]">Simulador de Debug</p>
                <p className="text-sm text-[#6a7282]">
                  {ativo ? '🟢 A simular aruba.txt' : '🔴 Desligado'}
                </p>
              </div>
              <button
                onClick={() => setSimOpen(false)}
                className="text-[#6a7282] hover:text-[#101828] text-xl font-bold"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-6 py-4 flex flex-col gap-3">
              {eventos.length === 0 && (
                <p className="text-sm text-[#6a7282]">A aguardar eventos...</p>
              )}
              {eventos.map((e, i) => (
                <div key={i} className="border border-[#e5e7eb] rounded-[12px] px-4 py-3 text-sm">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-[#101828]">{e.sensor} → {e.value}</span>
                    <span className="text-xs text-[#6a7282]">{e.timestamp?.slice(11, 19)}</span>
                  </div>
                  {e.prediction && !e.prediction.error && (
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`px-2 py-0.5 rounded-[8px] text-xs font-medium ${
                        e.prediction.is_anomaly
                          ? 'bg-[#fff1f2] text-[#ef4444]'
                          : 'bg-[#f0fdf4] text-[#10b981]'
                      }`}>
                        {e.prediction.expected_activity}
                      </span>
                      <span className="text-xs text-[#6a7282]">{e.prediction.confidence}%</span>
                      {e.ground_truth_activity && (
                        <span className="text-xs text-[#6a7282]">
                          {e.prediction.expected_activity === e.ground_truth_activity ? '✅' : '❌'} {e.ground_truth_activity}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export function OverviewPage() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-[#101828]">{t('overview.title')}</h1>

      <SafetyStatusHeader />
      <DebugModeButton />

      <div className="grid grid-cols-2 gap-6">
        <ResidentActivityCard />
        <EnvironmentalHealthCard />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <RecentAlertsCard />
        <DeviceStatusCard />
      </div>
    </div>
  )
}
