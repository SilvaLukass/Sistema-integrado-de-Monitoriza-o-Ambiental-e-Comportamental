import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { Activity, Camera, Cpu, DoorOpen, Droplets, Thermometer, Wifi, Wind, X } from 'lucide-react'
import { captureCameraFrame, getDevices, getSystemMetrics, type DeviceStatus } from '../api/backend'
import { useAppStore } from '../store/appStore'

function formatDuration(seconds: number) {
  const days = Math.floor(seconds / 86_400)
  const hours = Math.floor((seconds % 86_400) / 3600)
  return days > 0 ? `${days}d ${hours}h` : `${hours}h`
}

function formatLastSeen(lastSeen: string | null) {
  if (!lastSeen) return 'sem dados'
  const minutes = Math.max(0, Math.round((Date.now() - new Date(lastSeen).getTime()) / 60_000))
  if (minutes < 1) return 'agora mesmo'
  return `há ${minutes} min`
}

function iconForDevice(device: DeviceStatus) {
  if (device.type === 'door') return <DoorOpen size={20} className="text-[#10b981]" />
  if (device.type === 'airQuality' || device.id === 'CO2') return <Wind size={20} className="text-[#10b981]" />
  if (device.type === 'temperature') return <Thermometer size={20} className="text-[#10b981]" />
  if (device.type === 'humidity') return <Droplets size={20} className="text-[#10b981]" />
  return <Activity size={20} className="text-[#10b981]" />
}

function CameraCaptureCard() {
  const { t } = useTranslation()
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    return () => {
      if (imageUrl) URL.revokeObjectURL(imageUrl)
    }
  }, [imageUrl])

  async function handleCapture() {
    setIsLoading(true)
    setError(null)
    try {
      const blob = await captureCameraFrame()
      const nextUrl = URL.createObjectURL(blob)
      setImageUrl((currentUrl) => {
        if (currentUrl) URL.revokeObjectURL(currentUrl)
        return nextUrl
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : t('deviceStatus.cameraError'))
    } finally {
      setIsLoading(false)
    }
  }

  function closePreview() {
    setImageUrl((currentUrl) => {
      if (currentUrl) URL.revokeObjectURL(currentUrl)
      return null
    })
  }

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="size-12 bg-[rgba(37,99,235,0.1)] rounded-[14px] flex items-center justify-center shrink-0">
            <Camera size={24} className="text-[#2563eb]" />
          </div>
          <div>
            <p className="font-semibold text-lg text-[#101828]">{t('deviceStatus.cameraTitle')}</p>
            <p className="text-sm text-[#6a7282] mt-1">{t('deviceStatus.cameraSubtitle')}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleCapture}
          disabled={isLoading}
          className="bg-[#2563eb] disabled:bg-[#9ca3af] text-white font-semibold text-sm px-4 py-2 rounded-[12px] transition-colors"
        >
          {isLoading ? t('deviceStatus.cameraLoading') : t('deviceStatus.cameraButton')}
        </button>
      </div>

      {error && <p className="text-sm text-[#dc2626]">{error}</p>}

      {imageUrl && (
        <div className="fixed inset-0 bg-black/55 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-[14px] shadow-xl max-w-2xl w-full overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-[#e5e7eb]">
              <div>
                <p className="font-semibold text-lg text-[#101828]">{t('deviceStatus.cameraPreviewTitle')}</p>
                <p className="text-xs text-[#6a7282]">{t('deviceStatus.cameraPrivacyNote')}</p>
              </div>
              <button
                type="button"
                onClick={closePreview}
                className="size-9 rounded-full hover:bg-[#f3f4f6] flex items-center justify-center"
                aria-label={t('deviceStatus.cameraClose')}
              >
                <X size={20} className="text-[#4a5565]" />
              </button>
            </div>
            <img src={imageUrl} alt={t('deviceStatus.cameraAlt')} className="w-full object-contain bg-black" />
          </div>
        </div>
      )}
    </div>
  )
}

function RaspberryPiCard({ simpleMode }: { simpleMode: boolean }) {
  const { t } = useTranslation()
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['system-metrics'],
    queryFn: getSystemMetrics,
    refetchInterval: 15_000,
  })

  const isOnline = Boolean(data) && !isError
  const temperatureSubtitle =
    data?.temperature === null || data?.temperature === undefined
      ? t('deviceStatus.temperatureUnavailable')
      : data.temperature >= 70
        ? t('deviceStatus.highTemperature')
        : t('deviceStatus.withinLimits')

  const rpiMetrics = data
    ? [
        { label: t('deviceStatus.cpuUsage'), value: `${Math.round(data.cpu_usage)}%`, percentage: Math.round(data.cpu_usage) },
        { label: t('deviceStatus.memoryUsage'), value: `${Math.round(data.memory_usage)}%`, percentage: Math.round(data.memory_usage) },
        {
          label: t('deviceStatus.temperature'),
          value: data.temperature === null ? 'N/D' : `${Math.round(data.temperature)}°C`,
          subtitle: temperatureSubtitle,
        },
        { label: t('deviceStatus.uptime'), value: formatDuration(data.uptime_seconds), subtitle: t('deviceStatus.daysHours') },
      ]
    : []

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="size-12 bg-[rgba(37,99,235,0.1)] rounded-[14px] flex items-center justify-center shrink-0">
            <Cpu size={24} className="text-[#2563eb]" />
          </div>
          <div>
            <p className="font-semibold text-lg text-[#101828]">{t('deviceStatus.rpiController')}</p>
            <p className="text-sm text-[#6a7282]">
              {t('deviceStatus.rpiSubtitle')} · {data?.source ?? t('deviceStatus.metricsLoading')}
            </p>
          </div>
        </div>
        <span
          className={`font-semibold text-base px-4 py-2 rounded-[14px] ${
            isOnline
              ? 'bg-[#f0fdf4] text-[#10b981]'
              : 'bg-[#f3f4f6] text-[#6a7282]'
          }`}
        >
          {isLoading ? t('deviceStatus.metricsLoading') : isOnline ? t('status.online') : t('status.offline')}
        </span>
      </div>

      {isError && (
        <p className="text-sm text-[#dc2626]">
          {error instanceof Error ? error.message : t('deviceStatus.metricsError')}
        </p>
      )}

      {!simpleMode && (
        <div className="grid grid-cols-4 gap-4">
          {rpiMetrics.map((metric) => (
            <div key={metric.label} className="bg-[#f9fafb] rounded-[14px] p-4">
              <p className="text-sm text-[#4a5565]">{metric.label}</p>
              <p className="font-semibold text-2xl text-[#101828] mt-2">{metric.value}</p>

              {metric.percentage !== undefined ? (
                <div className="mt-2 h-2 bg-[#e5e7eb] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#2563eb] rounded-full transition-all duration-500"
                    style={{ width: `${metric.percentage}%` }}
                  />
                </div>
              ) : (
                <p className="text-xs text-[#6a7282] mt-2">{metric.subtitle}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ConnectedSensorsCard({ simpleMode, devices }: { simpleMode: boolean; devices: DeviceStatus[] }) {
  const { t } = useTranslation()
  const visibleDevices = devices
  const onlineCount = devices.filter((sensor) => sensor.online).length

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <div>
        <p className="font-semibold text-lg text-[#101828]">{t('deviceStatus.connectedSensors')}</p>
        <p className="text-sm text-[#6a7282] mt-1">
          {t('deviceStatus.sensorsOnline', { online: onlineCount, total: devices.length })}
        </p>
      </div>

      <div className={simpleMode ? 'flex flex-col gap-3' : 'grid grid-cols-2 xl:grid-cols-3 gap-4'}>
        {visibleDevices.map((sensor) => (
          <div
            key={sensor.id}
            className={
              simpleMode
                ? 'border border-[#e5e7eb] rounded-[14px] p-4 flex items-center justify-between'
                : 'border-2 border-[#e5e7eb] rounded-[14px] p-5 flex flex-col gap-4'
            }
          >
            <div className={simpleMode ? 'flex items-center gap-3' : 'flex items-start gap-3'}>
              <div className={`${simpleMode ? 'size-8' : 'size-10'} bg-[#f0fdf4] rounded-[14px] flex items-center justify-center shrink-0`}>
                {iconForDevice(sensor)}
              </div>
              <div>
                <p className="font-semibold text-base text-[#101828] leading-tight">{sensor.name}</p>
                {!simpleMode && <p className="text-xs text-[#6a7282] mt-1">{sensor.type}</p>}
              </div>
            </div>

            {simpleMode ? (
              <span className={`text-xs font-medium px-2 py-1 rounded-[10px] ${sensor.online ? 'bg-[#f0fdf4] text-[#10b981]' : 'bg-[#f3f4f6] text-[#6a7282]'}`}>
                {sensor.online ? t('status.online') : t('status.offline')}
              </span>
            ) : (
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-[#4a5565]">{t('deviceStatus.state')}</p>
                  <p className={`text-sm font-semibold ${sensor.online ? 'text-[#10b981]' : 'text-[#6a7282]'}`}>
                    {sensor.online ? t('status.online') : t('status.offline')}
                  </p>
                </div>

                <div className="border-t border-[#e5e7eb] pt-3 flex items-center justify-between">
                  <p className="text-xs text-[#6a7282]">{t('deviceStatus.lastUpdate')}</p>
                  <p className="text-xs font-medium text-[#364153]">{formatLastSeen(sensor.last_seen)}</p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function AllDevicesCard({ simpleMode, devices }: { simpleMode: boolean; devices: DeviceStatus[] }) {
  const { t } = useTranslation()
  const onlineCount = devices.filter((device) => device.online).length

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <div className="size-10 bg-[#eff6ff] rounded-[14px] flex items-center justify-center shrink-0">
          <Wifi size={20} className="text-[#2563eb]" />
        </div>
        <div>
          <p className="font-semibold text-lg text-[#101828]">{t('deviceStatus.allDevices')}</p>
          <p className="text-sm text-[#6a7282]">{t('deviceStatus.devicesOnline', { online: onlineCount, total: devices.length })}</p>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {devices.map((device) => (
          <div key={device.id} className="border border-[#e5e7eb] rounded-[14px] px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Wifi size={20} className={device.online ? 'text-[#2563eb]' : 'text-[#9ca3af]'} />
                <div>
                  <p className="font-semibold text-base text-[#101828]">{device.name}</p>
                  {!simpleMode && <p className="text-sm text-[#6a7282]">{device.room}</p>}
                </div>
              </div>
              <span className={`text-xs font-medium px-2 py-1 rounded-[10px] ${
                device.online
                  ? 'bg-[#f0fdf4] text-[#10b981]'
                  : 'bg-[#f3f4f6] text-[#6a7282]'
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

export function DeviceStatusPage() {
  const { t } = useTranslation()
  const simpleMode = useAppStore((state) => state.simpleMode)
  const { data: devices = [] } = useQuery({
    queryKey: ['devices'],
    queryFn: getDevices,
    refetchInterval: 5_000,
  })

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-[#101828]">{t('deviceStatus.title')}</h1>
        <p className="text-sm text-[#4a5565] mt-1">{t('deviceStatus.subtitle')}</p>
      </div>

      <RaspberryPiCard simpleMode={simpleMode} />
      <CameraCaptureCard />
      <ConnectedSensorsCard simpleMode={simpleMode} devices={devices} />
      <AllDevicesCard simpleMode={simpleMode} devices={devices} />
    </div>
  )
}
