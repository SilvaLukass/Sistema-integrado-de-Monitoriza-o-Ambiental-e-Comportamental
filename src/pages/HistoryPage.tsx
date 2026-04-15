import { useTranslation } from 'react-i18next'
import { AirQualityGauge } from '../components/AirQualityGauge'

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'
import { Activity } from 'lucide-react'
import { OccupancyHeatmap } from '../components/OccupancyHeatmap'
import { AdvancedHistoryChart } from './AdvancedHistoryChart'

interface HourlyData {
  hora: string
  eventos: number
}
// Simula eventos de movimento detetados por hora ao longo de 24h.
// Quando ligarmos ao HA, este array vem de um fetch à API.

const mockHourlyData: HourlyData[] = [
  { hora: '00:00', eventos: 2 },
  { hora: '01:00', eventos: 0 },
  { hora: '02:00', eventos: 0 },
  { hora: '03:00', eventos: 1 },
  { hora: '04:00', eventos: 0 },
  { hora: '05:00', eventos: 3 },
  { hora: '06:00', eventos: 8 },
  { hora: '07:00', eventos: 15 },
  { hora: '08:00', eventos: 22 },
  { hora: '09:00', eventos: 18 },
  { hora: '10:00', eventos: 14 },
  { hora: '11:00', eventos: 16 },
  { hora: '12:00', eventos: 20 },
  { hora: '13:00', eventos: 17 },
  { hora: '14:00', eventos: 28 },
  { hora: '15:00', eventos: 24 },
  { hora: '16:00', eventos: 19 },
  { hora: '17:00', eventos: 21 },
  { hora: '18:00', eventos: 16 },
  { hora: '19:00', eventos: 12 },
  { hora: '20:00', eventos: 9 },
  { hora: '21:00', eventos: 7 },
  { hora: '22:00', eventos: 4 },
  { hora: '23:00', eventos: 2 },
]

const totalEventos = mockHourlyData.reduce((sum, d) => sum + d.eventos, 0)
const picoHora = mockHourlyData.reduce((max, d) => d.eventos > max.eventos ? d : max)
const mediaHora = Math.round(totalEventos / mockHourlyData.length)

// nunca trabalhei com esta library, estes comentários podem ficar para percebermos um bocado melhor
// O Recharts passa as props automaticamente ao componente de tooltip.
// 'active' é true quando o rato está sobre o gráfico.
// 'payload' é o array de pontos sob o cursor — usamos payload[0].

interface TooltipProps {
  active?: boolean
  payload?: Array<{ value: number }>
  label?: string
}

function CustomTooltip({ active, payload, label }: TooltipProps) {
  const { t } = useTranslation()
  if (!active || !payload?.length) return null

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[10px] px-3 py-2 shadow-md">
      <p className="text-xs text-[#6a7282]">{label}</p>
      <p className="text-sm font-semibold text-[#101828]">
        {payload[0].value} {t('history.events')}
      </p>
    </div>
  )
}

function ActivityTrendsChart() {
  const { t } = useTranslation()

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <div className="size-10 bg-[#eff6ff] rounded-[14px] flex items-center justify-center shrink-0">
          <Activity size={20} className="text-[#2563eb]" />
        </div>
        <div>
          <p className="font-semibold text-lg text-[#101828]">{t('history.activityTrends')}</p>
          <p className="text-sm text-[#6a7282]">{t('history.movementPatterns24h')}</p>
        </div>
      </div>

      {/* Gráfico de área
          ResponsiveContainer com height fixo e width="100%" é o padrão correto.
          Nunca uses width fixo — quebra em ecrãs diferentes. */}
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={mockHourlyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>

          {/* defs: define um gradiente SVG reutilizável pelo id "gradienteAtividade"
              O gradiente vai de azul com 30% opacidade em cima até transparente em baixo.
              Isto dá o efeito de "área preenchida" suave que vês no mockup. */}
          <defs>
            <linearGradient id="gradienteAtividade" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
            </linearGradient>
          </defs>

          {/* CartesianGrid: as linhas horizontais de fundo.
              strokeDasharray="3 3" cria linhas tracejadas (3px linha, 3px espaço).
              vertical={false} remove as linhas verticais — mais limpo. */}
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />

          {/* XAxis: controla o eixo horizontal.
              dataKey diz ao Recharts qual campo do objeto usar como label.
              tickLine={false} e axisLine={false} removem as pequenas linhas dos ticks. */}
          <XAxis
            dataKey="hora"
            tick={{ fontSize: 11, fill: '#6a7282' }}
            tickLine={false}
            axisLine={false}
            interval={3}
          />

          {/* YAxis: eixo vertical com unidade "eventos"
              tickFormatter adiciona " ev" depois de cada número */}
          <YAxis
            tick={{ fontSize: 11, fill: '#6a7282' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${v}`}
          />

          {/* Tooltip: usa o nosso componente personalizado acima */}
          <Tooltip content={<CustomTooltip />} />

          {/* Area: a série de dados.
              type="monotone" suaviza a linha (vs "linear" que seria reto entre pontos).
              fill="url(#gradienteAtividade)" referencia o gradiente SVG que definimos.
              strokeWidth={2} define a espessura da linha. */}
          <Area
            type="monotone"
            dataKey="eventos"
            stroke="#2563eb"
            strokeWidth={2}
            fill="url(#gradienteAtividade)"
            dot={false}
            activeDot={{ r: 4, fill: '#2563eb' }}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Estatísticas em baixo — calculadas dinamicamente a partir dos dados */}
      <div className="grid grid-cols-3 divide-x divide-[#e5e7eb] border-t border-[#e5e7eb] pt-4">
        <div className="text-center">
          <p className="text-xs text-[#6a7282]">{t('history.peakActivity')}</p>
          <p className="font-semibold text-xl text-[#101828] mt-1">{picoHora.hora}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-[#6a7282]">{t('history.totalEvents')}</p>
          <p className="font-semibold text-xl text-[#101828] mt-1">{totalEventos}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-[#6a7282]">{t('history.averagePerHour')}</p>
          <p className="font-semibold text-xl text-[#101828] mt-1">{mediaHora}</p>
        </div>
      </div>
    </div>
  )
}

export function HistoryPage() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-[#101828]">{t('history.title')}</h1>
        <p className="text-sm text-[#6a7282] mt-1">{t('history.subtitle')}</p>
      </div>

      <div className="grid grid-cols-[3fr_1fr] gap-6">
        <AdvancedHistoryChart />
        <AirQualityGauge score={100} />
      </div>

      <OccupancyHeatmap />

    </div>
  )
}
