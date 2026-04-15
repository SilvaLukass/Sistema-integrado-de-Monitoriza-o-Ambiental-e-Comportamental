import { useTranslation } from 'react-i18next'
import { ShieldCheck, Activity, Leaf, Bell, Cpu, Wifi, AlertTriangle, Flame } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import type { Alert, AlertSeverity } from '../types'
import { getAlerts } from '../api/backend'
import { useAppStore } from '../store/appStore'
import { useState, useEffect } from 'react'


// tipos locais
// Definir os tipos aqui (e não em types/index.ts) porque são específicos
// desta página — não fazem sentido noutro contexto.

interface ActivityEvent {
  room: string
  time: string
  description: string
  sensorLabel: string
  sensorColor: 'blue' | 'purple'
}

interface EnvMetric {
  label: string
  value: string
  unit: string
  min: string
  max: string
  status: 'good' | 'warning' | 'danger'
  percentage: number
}

interface DeviceItem {
  id: string
  name: string
  room: string
  online: boolean
  battery: number
  lastSeen: string
}
//Interface exclusiva para a resposta do Modelo
interface AIResponse {
  expected_activity: string
  confidence: number
  is_anomaly: boolean
  message: string
}

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
//Alterada para reagir conforme o modelo responder
function SafetyStatusHeader() {
  const { t } = useTranslation()
  const [aiStatus, setAiStatus] = useState<any>(null)
  const [error, setError] = useState<boolean>(false)

  // Descobrir a hora atual
  const currentHour = new Date().getHours();

  // Simular sensores de forma inteligente baseada na hora!
  const currentSensorData = {
    "hour": currentHour,
    "day_of_week": new Date().getDay(),
    "M003": currentHour >= 23 || currentHour <= 7 ? 1.0 : 0.0, // Movimento na cama de noite
    "T001": 22.5,
    // Simulamos o pico de CO2 apenas à hora de jantar (19h ou 20h)
    "CO2": (currentHour === 19 || currentHour === 20) ? 1600 : 450
  }

  useEffect(() => {
    const checkAI = async () => {
      try {
        const res = await fetch('http://localhost:8000/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ readings: currentSensorData }),
        })

        if (!res.ok) throw new Error("API falhou")
        const data = await res.json()
        setAiStatus(data)
        setError(false)
      } catch (e) {
        console.error(e)
        setError(true)
      }
    }

    checkAI()
    const interval = setInterval(checkAI, 5000)
    return () => clearInterval(interval)
  }, [])

  // 1. Lógica de Anomalia da IA (Comportamento)
  const isRoutineAnomaly = aiStatus?.is_anomaly;

  // 2. Lógica de Perigo Ambiental (CO2 > 1200 = Mau/Perigoso)
  // No futuro, este valor virá dos teus sensores reais.
  const isAirQualityDanger = currentSensorData.CO2 > 1200;

  // Se houver QUALQUER um dos problemas, o ecrã fica vermelho.
  const isDanger = isRoutineAnomaly || isAirQualityDanger;

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
              <Flame size={32} className={textColor} /> // Ícone diferente se o perigo for só ambiental
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
              {error ? 'A tentar ligar à Inteligência Artificial...' :
                aiStatus ? (
                  <>
                    {/* Se for perigo de CO2, destacamos isso primeiro */}
                    {isAirQualityDanger && (
                      <span className="font-bold text-red-600 block mb-1">
                        Níveis de CO2 atuais: {currentSensorData.CO2} ppm
                      </span>
                    )}
                    A prever <strong>{t(`activities.${aiStatus.expected_activity}`, { defaultValue: aiStatus.expected_activity })}</strong><br></br>
                    <span className="text-xs italic text-gray-500">
                      Baseado {aiStatus.reason || "nos padrões recentes."}
                    </span>
                  </>
                ) : 'A analisar sensores...'}
            </p>

            {aiStatus && !error && (
              <button
                onClick={() => alert("Feedback guardado! A sua correção será usada para treinar o modelo na próxima semana.")}
                className="mt-3 text-xs font-medium text-[#2563eb] hover:text-blue-800 underline transition-colors"
              >
                A atividade não é esta? Corrigir IA
              </button>
            )}
          </div>
        </div>

        {aiStatus && !error && (
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

function ResidentActivityCard() {
  const { t } = useTranslation()

  // ─── Mock data ─────────────────────────────────────────────────────────────────
  // Quando ligarmos ao Home Assistant, só mudamos isto.
  const mockActivity: ActivityEvent[] = [
    { room: t('rooms.livingRoom'), time: '14:45', description: t('sensors.movementDetected'), sensorLabel: t('sensors.pir'), sensorColor: 'blue' },
    { room: t('rooms.kitchen'), time: '14:30', description: t('sensors.movementDetected'), sensorLabel: t('sensors.pir'), sensorColor: 'blue' },
    { room: t('rooms.mainDoor'), time: '13:15', description: t('sensors.doorOpened'), sensorLabel: t('sensors.door'), sensorColor: 'purple' },
    { room: t('rooms.bedroom'), time: '12:30', description: t('sensors.movementDetected'), sensorLabel: t('sensors.pir'), sensorColor: 'blue' },
  ]

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <CardHeader
        icon={<Activity size={20} className="text-[#2563eb]" />}
        title={t('overview.residentActivity')}
        subtitle={t('overview.recentMovements')}
        iconBg="bg-[#eff6ff]"
      />

      <div className="flex flex-col gap-4">
        {mockActivity.map((event, index) => (
          <div key={index} className="flex gap-4">
            <div className="flex flex-col items-center w-3 shrink-0">
              <div className="size-3 rounded-full bg-[#2563eb] shrink-0" />
              {index < mockActivity.length - 1 && (
                <div className="w-0.5 flex-1 bg-[#e5e7eb] mt-1" />
              )}
            </div>

            <div className="pb-4 flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="font-medium text-base text-[#101828]">{event.room}</p>
                <p className="text-sm text-[#6a7282]">{event.time}</p>
              </div>
              <p className="text-sm text-[#4a5565] mt-1">{event.description}</p>
              <span className={`inline-block mt-2 px-3 py-1 rounded-[10px] text-xs font-medium
                ${event.sensorColor === 'blue'
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

function EnvironmentalHealthCard() {
  const { t } = useTranslation()

  const statusColors = {
    good: { bar: 'bg-[#10b981]', badge: 'bg-[rgba(16,185,129,0.13)] text-[#10b981]', label: t('status.good') },
    warning: { bar: 'bg-[#f59e0b]', badge: 'bg-[#fffbeb] text-[#f59e0b]', label: t('status.warning') },
    danger: { bar: 'bg-[#ef4444]', badge: 'bg-[#fff1f2] text-[#ef4444]', label: t('status.danger') },
  }

  const mockEnvMetrics: EnvMetric[] = [
    { label: t('sensors.co2'), value: '450', unit: 'ppm', min: '0 ppm', max: '2000 ppm', status: 'good', percentage: 22 },
    { label: t('sensors.temperature'), value: '22', unit: '°C', min: '18°C', max: '28°C', status: 'good', percentage: 60 },
  ]

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <CardHeader
        icon={<Leaf size={20} className="text-[#10b981]" />}
        title={t('overview.environmentalHealth')}
        subtitle={t('overview.airQualityTemp')}
        iconBg="bg-[#f0fdf4]"
      />

      <div className="flex flex-col gap-6">
        {mockEnvMetrics.map((metric) => {
          const colors = statusColors[metric.status]
          return (
            <div key={metric.label}>
              <div className="flex items-center justify-between mb-3">
                <p className="font-medium text-base text-[#101828]">{metric.label}</p>
                <p className="font-semibold text-2xl text-[#101828]">
                  {metric.value}<span className="text-base ml-1">{metric.unit}</span>
                </p>
              </div>

              {/* Barra de progresso */}
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
  })

  const fallbackAlerts: Alert[] = [
    { id: '1', title: t('alerts.noActivity'), description: t('alerts.noMovement'), timestamp: new Date().toISOString(), severity: 'warning', resolved: false },
    { id: '2', title: t('alerts.tempResolved'), description: t('alerts.tempResolvedDesc'), timestamp: new Date().toISOString(), severity: 'success', resolved: true },
    { id: '3', title: t('alerts.dailyCheck'), description: t('alerts.dailyCheckDesc'), timestamp: new Date().toISOString(), severity: 'info', resolved: true },
  ]

  const renderedAlerts = (alerts.length > 0 ? alerts : fallbackAlerts).slice(0, 3)

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <CardHeader
        icon={<Bell size={20} className="text-[#f59e0b]" />}
        title={t('overview.recentAlerts')}
        subtitle={t('overview.last24h')}
        iconBg="bg-[#fffbeb]"
      />

      <div className="flex flex-col gap-3">
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

function DeviceStatusCard() {
  const { t } = useTranslation()
  const simpleMode = useAppStore((state) => state.simpleMode)

  const mockDevices: DeviceItem[] = [
    { id: '1', name: `${t('sensors.pir')} - ${t('rooms.livingRoom')}`, room: t('rooms.livingRoom'), online: true, battery: 87, lastSeen: t('common.minutesAgo', { count: 2 }) },
    { id: '2', name: `${t('sensors.door')} - ${t('rooms.mainDoor')}`, room: t('rooms.mainEntrance'), online: true, battery: 92, lastSeen: t('common.minutesAgo', { count: 5 }) },
    { id: '3', name: `${t('sensors.pir')} - ${t('rooms.bedroom')}`, room: t('rooms.bedroom'), online: true, battery: 78, lastSeen: t('common.minutesAgo', { count: 1 }) },
  ]

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <CardHeader
        icon={<Cpu size={20} className="text-[#2563eb]" />}
        title={t('overview.deviceStatus')}
        subtitle={t('overview.devicesOnline', { online: mockDevices.filter(d => d.online).length, total: mockDevices.length })}
        iconBg="bg-[#eff6ff]"
      />

      <div className="flex flex-col gap-3">
        {mockDevices.map((device) => (
          <div key={device.id} className="border border-[#e5e7eb] rounded-[14px] px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Wifi size={20} className={device.online ? 'text-[#2563eb] shrink-0' : 'text-[#9ca3af] shrink-0'} />
                <div>
                  <p className="font-semibold text-base text-[#101828]">{device.name}</p>
                  {!simpleMode && <p className="text-sm text-[#6a7282]">{device.room}</p>}
                </div>
              </div>
              {simpleMode ? (
                <span className={`text-xs font-medium px-2 py-1 rounded-[10px] ${device.online ? 'bg-[#f0fdf4] text-[#10b981]' : 'bg-[#f3f4f6] text-[#6a7282]'
                  }`}>
                  {device.online ? t('status.online') : t('status.offline')}
                </span>
              ) : (
                <p className="text-sm font-medium text-[#4a5565]">{device.battery}%</p>
              )}
            </div>

            {!simpleMode && (
              <div className="flex items-center justify-between mt-3">
                <span className={`text-xs font-medium px-2 py-1 rounded-[10px] ${device.online ? 'bg-[#f0fdf4] text-[#10b981]' : 'bg-[#f3f4f6] text-[#6a7282]'
                  }`}>
                  {device.online ? t('status.online') : t('status.offline')}
                </span>
                <p className="text-xs text-[#6a7282]">{t('common.lastSeenTime', { time: device.lastSeen })}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Página principal ──────────────────────────────────────────────────────────
export function OverviewPage() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-[#101828]">{t('overview.title')}</h1>

      <SafetyStatusHeader />

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
