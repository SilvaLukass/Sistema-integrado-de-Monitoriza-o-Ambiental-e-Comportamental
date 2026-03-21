import { useTranslation } from 'react-i18next'
import { Cpu, Wifi, Wind, DoorOpen, Activity, BatteryMedium } from 'lucide-react'

interface RpiMetric {
  label: string
  value: string
  subtitle?: string
  percentage?: number
}

interface SensorCard {
  id: string
  name: string
  model: string
  icon: React.ReactNode
  online: boolean
  metrics: { label: string; value: string }[]
  lastUpdated: string
}

interface DeviceRow {
  id: string
  name: string
  room: string
  online: boolean
  battery: number
  lastSeen: string
}


function RaspberryPiCard() {
  const { t } = useTranslation()

  const rpiMetrics: RpiMetric[] = [
    { label: t('deviceStatus.cpuUsage'),      value: '34%', percentage: 34 },
    { label: t('deviceStatus.memoryUsage'),  value: '56%', percentage: 56 },
    { label: t('deviceStatus.temperature'),     value: '42°C', subtitle: t('deviceStatus.withinLimits') },
    { label: t('deviceStatus.uptime'),     value: '12:08', subtitle: t('deviceStatus.daysHours') },
  ]

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="size-12 bg-[rgba(37,99,235,0.1)] rounded-[14px] flex items-center justify-center shrink-0">
            <Cpu size={24} className="text-[#2563eb]" />
          </div>
          <div>
            <p className="font-semibold text-lg text-[#101828]">{t('deviceStatus.rpiController')}</p>
            <p className="text-sm text-[#6a7282]">{t('deviceStatus.rpiSubtitle')}</p>
          </div>
        </div>
        <span className="bg-[#f0fdf4] text-[#10b981] font-semibold text-base px-4 py-2 rounded-[14px]">
          {t('status.online')}
        </span>
      </div>

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
    </div>
  )
}

function ConnectedSensorsCard() {
  const { t } = useTranslation()

  const sensorCards: SensorCard[] = [
    {
      id: '1',
      name: t('deviceStatus.pirMotionSensor'),
      model: 'HC-SR501',
      icon: <Activity size={20} className="text-[#10b981]" />,
      online: true,
      metrics: [
        { label: t('deviceStatus.state'),  value: t('status.online') },
        { label: t('deviceStatus.battery'), value: '87%' },
      ],
      lastUpdated: t('common.minutesAgo', { count: 2 }),
    },
    {
      id: '2',
      name: t('deviceStatus.magneticDoorSensor'),
      model: 'Reed Switch',
      icon: <DoorOpen size={20} className="text-[#10b981]" />,
      online: true,
      metrics: [
        { label: t('deviceStatus.state'),  value: t('status.online') },
        { label: t('deviceStatus.battery'), value: '92%' },
      ],
      lastUpdated: t('common.minutesAgo', { count: 1 }),
    },
    {
      id: '3',
      name: t('deviceStatus.airQualitySensor'),
      model: 'Grove Air Quality',
      icon: <Wind size={20} className="text-[#10b981]" />,
      online: true,
      metrics: [
        { label: t('deviceStatus.state'), value: t('status.online') },
        { label: t('deviceStatus.temp'),   value: '22°C' },
      ],
      lastUpdated: t('common.justNow'),
    },
  ]

  const onlineCount = sensorCards.filter(s => s.online).length

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <div>
        <p className="font-semibold text-lg text-[#101828]">{t('deviceStatus.connectedSensors')}</p>
        <p className="text-sm text-[#6a7282] mt-1">{t('deviceStatus.sensorsOnline', { online: onlineCount, total: sensorCards.length })}</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {sensorCards.map((sensor) => (
          <div key={sensor.id} className="border-2 border-[#e5e7eb] rounded-[14px] p-5 flex flex-col gap-4">
            <div className="flex items-start gap-3">
              <div className="size-10 bg-[#f0fdf4] rounded-[14px] flex items-center justify-center shrink-0">
                {sensor.icon}
              </div>
              <div>
                <p className="font-semibold text-base text-[#101828] leading-tight">{sensor.name}</p>
                <p className="text-xs text-[#6a7282] mt-1">{sensor.model}</p>
              </div>
            </div>

            <div className="flex flex-col gap-3">
              {sensor.metrics.map((m) => (
                <div key={m.label} className="flex items-center justify-between">
                  <p className="text-sm text-[#4a5565]">{m.label}</p>
                  <p className={`text-sm font-semibold ${m.label === t('deviceStatus.state') ? 'text-[#10b981]' : 'text-[#101828]'}`}>
                    {m.value}
                  </p>
                </div>
              ))}

              <div className="border-t border-[#e5e7eb] pt-3 flex items-center justify-between">
                <p className="text-xs text-[#6a7282]">{t('deviceStatus.lastUpdate')}</p>
                <p className="text-xs font-medium text-[#364153]">{sensor.lastUpdated}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function AllDevicesCard() {
  const { t } = useTranslation()

  const deviceRows: DeviceRow[] = [
    { id: '1', name: `${t('sensors.pir')} - ${t('rooms.livingRoom')}`,  room: t('rooms.livingRoom'),    online: true,  battery: 87, lastSeen: t('common.minutesAgo', { count: 2 }) },
    { id: '2', name: `${t('sensors.door')} - ${t('rooms.mainDoor')}`,   room: t('rooms.mainEntrance'), online: true,  battery: 92, lastSeen: t('common.minutesAgo', { count: 5 }) },
    { id: '3', name: `${t('sensors.pir')} - ${t('rooms.bedroom')}`,     room: t('rooms.bedroom'),       online: true,  battery: 78, lastSeen: t('common.minutesAgo', { count: 1 }) },
    { id: '4', name: `${t('sensors.airQuality')} - ${t('rooms.livingRoom')}`, room: t('rooms.livingRoom'), online: true, battery: 95, lastSeen: t('common.justNow') },
    { id: '5', name: `${t('sensors.pir')} - ${t('rooms.kitchen')}`,     room: t('rooms.kitchen'),       online: false, battery: 64, lastSeen: t('common.minutesAgo', { count: 3 }) },
  ]

  const onlineCount = deviceRows.filter(d => d.online).length

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <div className="size-10 bg-[#eff6ff] rounded-[14px] flex items-center justify-center shrink-0">
          <Wifi size={20} className="text-[#2563eb]" />
        </div>
        <div>
          <p className="font-semibold text-lg text-[#101828]">{t('deviceStatus.allDevices')}</p>
          <p className="text-sm text-[#6a7282]">{t('deviceStatus.devicesOnline', { online: onlineCount, total: deviceRows.length })}</p>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {deviceRows.map((device) => (
          <div key={device.id} className="border border-[#e5e7eb] rounded-[14px] px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Wifi size={20} className={device.online ? 'text-[#2563eb]' : 'text-[#9ca3af]'} />
                <div>
                  <p className="font-semibold text-base text-[#101828]">{device.name}</p>
                  <p className="text-sm text-[#6a7282]">{device.room}</p>
                </div>
              </div>
              <div className="flex items-center gap-1 text-sm font-medium text-[#4a5565]">
                <BatteryMedium size={16} className="text-[#4a5565]" />
                {device.battery}%
              </div>
            </div>

            <div className="flex items-center justify-between mt-3">
              <span className={`text-xs font-medium px-2 py-1 rounded-[10px] ${
                device.online
                  ? 'bg-[#f0fdf4] text-[#10b981]'
                  : 'bg-[#f3f4f6] text-[#6a7282]'
              }`}>
                {device.online ? t('status.online') : t('status.offline')}
              </span>
              <p className="text-xs text-[#6a7282]">{t('common.lastSeenTime', { time: device.lastSeen })}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function DeviceStatusPage() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-[#101828]">{t('deviceStatus.title')}</h1>
        <p className="text-sm text-[#4a5565] mt-1">{t('deviceStatus.subtitle')}</p>
      </div>

      <RaspberryPiCard />
      <ConnectedSensorsCard />
      <AllDevicesCard />
    </div>
  )
}
