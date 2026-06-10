import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { LayoutGrid } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getOccupancyHeatmap, type OccupancyHeatmapCell } from '../api/backend'

const DAY_KEYS = [
  'days.monday', 'days.tuesday', 'days.wednesday', 'days.thursday',
  'days.friday', 'days.saturday', 'days.sunday',
]
const HOURS = Array.from({ length: 24 }, (_, i) => i)

// Converte um valor 0-100 numa cor.
// Abaixo de 5 → cinzento (sem atividade).
// Acima → azul primário com opacidade proporcional ao valor.
// Desta forma o gradiente é contínuo, não discreto.
function valueToColor(value: number): string {
  if (value < 5) return '#f3f4f6'
  const opacity = 0.15 + (value / 100) * 0.85
  return `rgba(37, 99, 235, ${opacity.toFixed(2)})`
}

// ─── Tooltip ──────────────────────────────────────────────────────────────────
// Estado de hover gerido no componente pai e passado como prop.
// Isto evita ter um useState por célula (168 estados) — seria caríssimo.

interface TooltipState {
  day: number
  hour: number
  value: number
  x: number
  y: number
}


export function OccupancyHeatmap() {
  const { t } = useTranslation()
  const [tooltip, setTooltip] = useState<TooltipState | null>(null)
  const { data = [] } = useQuery({
    queryKey: ['occupancy-heatmap'],
    queryFn: getOccupancyHeatmap,
    refetchInterval: 30_000,
  })

  const heatmapData: OccupancyHeatmapCell[] =
    data.length === 168
      ? data
      : Array.from({ length: 7 * 24 }, (_, idx) => ({
          day: Math.floor(idx / 24),
          hour: idx % 24,
          value: 0,
        }))

  const days = DAY_KEYS.map(key => t(key))

  const totalAtivo = heatmapData.reduce((sum, c) => sum + c.value, 0)
  const mediaAtividade = Math.round(totalAtivo / heatmapData.length)
  const maisAtivo = heatmapData.reduce((max, c) => (c.value > max.value ? c : max), heatmapData[0])
  const menosAtivo = heatmapData
    .filter(c => c.value > 5)
    .reduce((min, c) => c.value < min.value ? c : min, { value: 999, day: 0, hour: 0 })

  function getValueLabel(value: number): string {
    if (value < 5)  return t('heatmap.noActivity')
    if (value < 30) return t('heatmap.lowActivity')
    if (value < 60) return t('heatmap.moderateActivity')
    if (value < 85) return t('heatmap.highActivity')
    return t('heatmap.maxActivity')
  }

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      {/* Cabeçalho */}
      <div className="flex items-center gap-3">
        <div className="size-10 bg-[#eff6ff] rounded-[14px] flex items-center justify-center shrink-0">
          <LayoutGrid size={20} className="text-[#2563eb]" />
        </div>
        <div>
          <p className="font-semibold text-lg text-[#101828]">{t('heatmap.title')}</p>
          <p className="text-sm text-[#6a7282]">{t('heatmap.subtitle')}</p>
        </div>
      </div>

      {/* Grelha + labels
          Estrutura: coluna de labels dos dias à esquerda + área da grelha à direita */}
      <div className="relative overflow-hidden">

        {/* Labels das horas — 24 colunas alinhadas com a grelha abaixo.
            O pl-[72px] empurra as labels para alinhar com as células
            (72px = largura da coluna dos dias). */}
        <div className="flex pl-[72px] mb-1">
          {HOURS.map(hour => (
            <div key={hour} className="flex-1 text-center">
            <span className="text-[10px] text-[#6a7282]">{hour}</span>
            </div>
          ))}
        </div>

        {/* Linhas da grelha — uma por dia */}
        <div className="flex flex-col gap-1">
          {days.map((day, dayIndex) => (
            <div key={day} className="flex items-center gap-0">
              {/* Label do dia — largura fixa de 72px */}
              <span className="w-[72px] shrink-0 text-xs text-[#4a5565] pr-3 text-right">
                {day}
              </span>

              <div className="flex gap-1 flex-1">
                {HOURS.map(hour => {
                const cell = heatmapData.find(c => c.day === dayIndex && c.hour === hour)!
                return (
                <div
                    key={hour}
                    className="flex-1 aspect-square rounded-sm cursor-pointer transition-all hover:brightness-110 hover:ring-2 hover:ring-[#2563eb]/30"
                    style={{ backgroundColor: valueToColor(cell.value) }}
                    onMouseEnter={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect()
                    setTooltip({ day: dayIndex, hour, value: cell.value, x: rect.left + rect.width / 2, y: rect.top })
                    }}
                    onMouseLeave={() => setTooltip(null)}/>
                )
                 })}
                </div>
            </div>
          ))}
        </div>

        {tooltip && (
          <div
            className="fixed z-50 bg-[#101828] text-white text-xs rounded-[8px] px-3 py-2 pointer-events-none -translate-x-1/2 -translate-y-full -mt-2"
            style={{ left: tooltip.x, top: tooltip.y }}
          >
            <p className="font-medium">{days[tooltip.day]}, {String(tooltip.hour).padStart(2, '0')}:00</p>
            <p className="text-[#9ca3af] mt-0.5">{getValueLabel(tooltip.value)}</p>
            <p className="font-semibold mt-0.5">{tooltip.value}%</p>
          </div>
        )}
      </div>

      {/* Legenda de intensidade */}
      <div className="flex items-center justify-between pt-4 border-t border-[#e5e7eb]">
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#6a7282]">{t('heatmap.activityLevel')}</span>
          <div className="flex items-center gap-1 ml-2">
            <span className="text-xs text-[#6a7282]">{t('heatmap.low')}</span>
            {[5, 25, 50, 75, 100].map(v => (
              <div
                key={v}
                className="size-4 rounded-sm"
                style={{ backgroundColor: valueToColor(v) }}
              />
            ))}
            <span className="text-xs text-[#6a7282]">{t('heatmap.high')}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-[#f9fafb] rounded-[10px] px-4 py-3">
          <p className="text-xs text-[#6a7282]">{t('heatmap.mostActive')}</p>
          <p className="font-semibold text-sm text-[#101828] mt-1">
            {days[maisAtivo.day]}, {String(maisAtivo.hour).padStart(2, '0')}h
          </p>
        </div>
        <div className="bg-[#f9fafb] rounded-[10px] px-4 py-3">
          <p className="text-xs text-[#6a7282]">{t('heatmap.leastActive')}</p>
          <p className="font-semibold text-sm text-[#101828] mt-1">
            {days[menosAtivo.day]}, {String(menosAtivo.hour).padStart(2, '0')}h
          </p>
        </div>
        <div className="bg-[#f9fafb] rounded-[10px] px-4 py-3">
          <p className="text-xs text-[#6a7282]">{t('heatmap.averageActivity')}</p>
          <p className="font-semibold text-sm text-[#101828] mt-1">{mediaAtividade}%</p>
        </div>
      </div>
    </div>
  )
}
