import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle, Info } from 'lucide-react'
import type { Alert, AlertSeverity } from '../types'
import { getAlerts } from '../api/backend'

// Mapeia a severidade do alerta para as cores do design.
const severityStyles: Record<AlertSeverity, { bg: string; border: string; icon: React.ReactNode }> = {
  warning: {
    bg: 'bg-[#fffbeb]',
    border: 'border-[#fee685]',
    icon: <AlertTriangle size={20} className="text-[#f59e0b]" />,
  },
  success: {
    bg: 'bg-[#f0fdf4]',
    border: 'border-[#b9f8cf]',
    icon: <CheckCircle size={20} className="text-[#10b981]" />,
  },
  info: {
    bg: 'bg-[#eff6ff]',
    border: 'border-[#bedbff]',
    icon: <Info size={20} className="text-[#2563eb]" />,
  },
  danger: {
    bg: 'bg-[#fff1f2]',
    border: 'border-[#fecdd3]',
    icon: <AlertTriangle size={20} className="text-[#ef4444]" />,
  },
}

function AlertItem({ alert }: { alert: Alert }) {
  const style = severityStyles[alert.severity]
  const formattedTimestamp = useMemo(
    () =>
      new Date(alert.timestamp).toLocaleString('pt-PT', {
        dateStyle: 'short',
        timeStyle: 'short',
      }),
    [alert.timestamp],
  )

  return (
    <div className={`${style.bg} ${style.border} border rounded-[14px] px-4 py-4`}>
      <div className="flex items-start gap-3">
        <span className="mt-0.5 shrink-0">{style.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-4">
            <p className="font-semibold text-base text-[#101828]">{alert.title}</p>
            <p className="text-xs text-[#6a7282] shrink-0">{formattedTimestamp}</p>
          </div>
          <p className="text-sm text-[#4a5565] mt-1">{alert.description}</p>
        </div>
      </div>
    </div>
  )
}

export default function AlertsPage() {
  const { t } = useTranslation()

  const { data: alerts = [], isLoading, isError, error } = useQuery({
    queryKey: ['alerts'],
    queryFn: getAlerts,
  })
  const renderedAlerts: Alert[] = alerts

  return (
    <div>
      <h1 className="text-2xl font-semibold text-[#101828]">{t('alerts.title')}</h1>

      <div className="mt-6 bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="size-10 bg-[#fffbeb] rounded-[14px] flex items-center justify-center">
            <AlertTriangle size={20} className="text-[#f59e0b]" />
          </div>
          <div>
            <p className="font-semibold text-lg text-[#101828]">{t('alerts.recentAlerts')}</p>
            <p className="text-sm text-[#6a7282]">{t('alerts.last24h')}</p>
          </div>
        </div>

        {isLoading && (
          <p className="text-sm text-[#6a7282] mb-4">A carregar alertas do backend...</p>
        )}
        {isError && (
          <p className="text-sm text-[#b42318] mb-4">
            Erro ao carregar alertas: {(error as Error).message}
          </p>
        )}

        <div className="flex flex-col gap-3">
          {renderedAlerts.length === 0 && (
            <div className="border border-dashed border-[#d0d5dd] rounded-[14px] px-4 py-5 text-sm text-[#6a7282]">
              Sem alertas para mostrar.
            </div>
          )}
          {renderedAlerts.map((alert) => (
            <AlertItem key={alert.id} alert={alert} />
          ))}
        </div>
      </div>
    </div>
  )
}
