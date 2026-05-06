import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Activity, Flame } from 'lucide-react'
import { getSensorHistory } from '../api/backend'

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max)

export function ActivityTrendsChart() {
  const { t } = useTranslation()
  const [activeMetric, setActiveMetric] = useState<'all' | 'co2' | 'temp' | 'activity'>('all')
  const { data = [], isLoading, isError } = useQuery({
    queryKey: ['sensor-history', 24],
    queryFn: () => getSensorHistory(24),
  })
  const chartData = useMemo(
    () =>
      data.map((point) => ({
        ...point,
        tempIndex: Math.round(clamp(((point.tempHum - 10) / 30) * 100, 0, 100)),
        co2Index: point.co2 === null ? null : Math.round(clamp(((point.co2 - 400) / 1200) * 100, 0, 100)),
      })),
    [data]
  )
  const hasCO2Data = chartData.some((point) => point.co2 !== null)

  const getCO2Status = (ppm: number) => {
    if (ppm <= 800) return t('airQuality.good', 'Bom')
    if (ppm <= 1200) return t('airQuality.moderate', 'Atenção')
    return t('airQuality.bad', 'Mau/Perigoso')
  }

  const co2Label = t('sensors.co2Level', 'Níveis de CO2 (ppm)')
  const activityLabel = t('history.routineActivity', 'Atividade (Rotina)')
  const timeTicks = ['01:00', '03:00', '05:00', '07:00', '09:00', '11:00', '13:00', '15:00', '17:00', '19:00', '21:00', '23:00']
  const isCO2Only = activeMetric === 'co2'
  const isOverview = activeMetric === 'all'
  const showCO2Thresholds = hasCO2Data && (activeMetric === 'all' || activeMetric === 'co2')
  const leftAxisDomain = isCO2Only ? [400, 1600] : activeMetric === 'temp' ? [0, 70] : [0, 100]
  const leftAxisTicks = isCO2Only ? [400, 800, 1200, 1600] : activeMetric === 'temp' ? [0, 20, 40, 60] : [0, 25, 50, 75, 100]
  const co2DataKey = isOverview ? 'co2Index' : 'co2'
  const tempDataKey = isOverview ? 'tempIndex' : 'tempHum'
  const co2ReferenceLines = isOverview ? [33, 67] : [800, 1200]

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h3 className="font-semibold text-lg text-[#101828]">
            {t('history.multisensorAnalysis', 'Análise Multissensorial (24h)')}
          </h3>
          <p className="text-sm text-[#6a7282]">
            {t('history.multisensorDesc', 'Correlação entre Rotina, Ambiente e Qualidade do Ar')}
          </p>
        </div>

        <div className="flex bg-[#f3f4f6] rounded-lg p-1">
          <button
            onClick={() => setActiveMetric('all')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
              activeMetric === 'all' ? 'bg-white shadow-sm text-[#101828]' : 'text-[#6a7282]'
            }`}
          >
            {t('history.overview', 'Visão Geral')}
          </button>
          <button
            onClick={() => setActiveMetric('co2')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1 ${
              activeMetric === 'co2' ? 'bg-white shadow-sm text-[#ef4444]' : 'text-[#6a7282]'
            }`}
          >
            <Flame size={14} /> {t('sensors.gas', 'Gás / CO2')}
          </button>
          <button
            onClick={() => setActiveMetric('temp')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1 ${
              activeMetric === 'temp' ? 'bg-white shadow-sm text-[#ef4444]' : 'text-[#6a7282]'
            }`}
          >
            <Activity size={14} /> {t('sensors.temperature', 'Temperatura')}
          </button>
          <button
            onClick={() => setActiveMetric('activity')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1 ${
              activeMetric === 'activity' ? 'bg-white shadow-sm text-[#ef4444]' : 'text-[#6a7282]'
            }`}
          >
            <Activity size={14} /> {t('history.routineActivity', 'Atividade (Rotina)')}
          </button>
        </div>
      </div>

      <div className="flex min-h-8 flex-wrap items-center justify-end gap-2 text-xs font-semibold -mb-3">
        {showCO2Thresholds ? (
          <>
            {isOverview && <span className="rounded-full bg-slate-50 px-2 py-1 text-slate-600">{t('history.relativeIndex', 'Indice relativo 0-100')}</span>}
            <span className="rounded-full bg-emerald-50 px-2 py-1 text-emerald-700">{t('airQuality.good', 'Bom')} ≤ 800 ppm</span>
            <span className="rounded-full bg-amber-50 px-2 py-1 text-amber-700">
              {t('airQuality.moderate', 'Moderado')} 801-1200 ppm
            </span>
            <span className="rounded-full bg-red-50 px-2 py-1 text-red-700">{t('airQuality.bad', 'Mau')} &gt; 1200 ppm</span>
          </>
        ) : activeMetric === 'all' ? (
          <span className="rounded-full bg-slate-50 px-2 py-1 text-slate-600">
            {t('history.relativeIndex', 'Indice relativo 0-100')} · Aruba sem CO2
          </span>
        ) : activeMetric === 'co2' ? (
          <span className="rounded-full bg-slate-50 px-2 py-1 text-slate-600">
            Dataset Aruba nao contem sensor CO2
          </span>
        ) : (
          <span className="rounded-full bg-slate-50 px-2 py-1 text-slate-600">
            {activeMetric === 'temp' ? t('sensors.temperature', 'Temperatura') : t('history.routineActivity', 'Atividade (Rotina)')}
          </span>
        )}
      </div>

      <div className="h-[350px] w-full mt-4">
        {isLoading && <p className="text-sm text-[#6a7282]">A carregar histórico dos sensores...</p>}
        {isError && <p className="text-sm text-[#b42318]">Erro ao carregar histórico dos sensores.</p>}
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 16, right: 24, left: 8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
            <XAxis
              dataKey="time"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: '#6a7282' }}
              ticks={timeTicks}
              interval={0}
              padding={{ left: 8, right: 16 }}
              dy={10}
            />

            <YAxis
              yAxisId="left"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: isCO2Only ? '#ef4444' : '#6a7282', fontWeight: isCO2Only ? 600 : 400 }}
              width={46}
              domain={leftAxisDomain}
              ticks={leftAxisTicks}
            />

            {showCO2Thresholds && (
              <>
                <ReferenceLine yAxisId="left" y={co2ReferenceLines[0]} stroke="#10b981" strokeDasharray="3 3" strokeOpacity={0.35} />
                <ReferenceLine yAxisId="left" y={co2ReferenceLines[1]} stroke="#f59e0b" strokeDasharray="3 3" strokeOpacity={0.35} />
              </>
            )}

            <Tooltip
              formatter={(value, name, item) => {
                const numericValue = Number(value)
                const payload = item?.payload
                if (name === co2Label) {
                  const co2Value = Number(payload?.co2 ?? numericValue)
                  return [`${co2Value} ppm (${getCO2Status(co2Value)})`, t('sensors.airQuality', 'Qualidade do Ar')]
                }
                if (name === activityLabel) {
                  return [`${numericValue}%`, name]
                }
                if (name === t('sensors.temperature', 'Temp / Humidade')) {
                  const tempValue = Number(payload?.tempHum ?? numericValue)
                  return [tempValue, name]
                }
                return [numericValue, name]
              }}
              contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
              labelStyle={{ fontWeight: 'bold', color: '#101828', marginBottom: '4px' }}
            />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />

            {(activeMetric === 'all' || activeMetric === 'activity') && (
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="movement"
                name={activityLabel}
                stroke="#3b82f6"
                fill="#eff6ff"
                strokeWidth={2}
              />
            )}

            {(activeMetric === 'all' || activeMetric === 'temp') && (
              <Line
                yAxisId="left"
                type="monotone"
                dataKey={tempDataKey}
                name={t('sensors.temperature', 'Temp / Humidade')}
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
              />
            )}

            {hasCO2Data && (activeMetric === 'all' || activeMetric === 'co2') && (
              <Line
                yAxisId="left"
                type="monotone"
                dataKey={co2DataKey}
                name={co2Label}
                stroke="#ef4444"
                strokeWidth={2}
                dot={{ r: 3, fill: '#ef4444' }}
                activeDot={{ r: 6 }}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-[#e5e7eb]">
        <div className="flex gap-3 items-start">
          <div className="mt-1 size-8 rounded-full bg-[#eff6ff] flex items-center justify-center shrink-0">
            <Activity size={16} className="text-[#3b82f6]" />
          </div>
          <div>
            <p className="text-sm font-semibold text-[#101828]">{t('history.sleepPatternTitle', 'Padrão de Sono')}</p>
            <p className="text-xs text-[#6a7282] mt-0.5">
              {t('history.sleepPatternDesc', 'Atividade mínima durante a madrugada, dentro do esperado.')}
            </p>
          </div>
        </div>

        <div className="flex gap-3 items-start">
          <div className="mt-1 size-8 rounded-full bg-[#fffbeb] flex items-center justify-center shrink-0">
            <Activity size={16} className="text-[#f59e0b]" />
          </div>
          <div>
            <p className="text-sm font-semibold text-[#101828]">{t('history.activityPatternTitle', 'Rotina Diária')}</p>
            <p className="text-xs text-[#6a7282] mt-0.5">
              {t('history.activityPatternDesc', 'Picos de atividade concentrados de manhã e ao fim da tarde.')}
            </p>
          </div>
        </div>

        <div className="flex gap-3 items-start">
          <div className="mt-1 size-8 rounded-full bg-[#fff1f2] flex items-center justify-center shrink-0">
            <Flame size={16} className="text-[#ef4444]" />
          </div>
          <div>
            <p className="text-sm font-semibold text-[#101828]">{t('history.airQualityPatternTitle', 'Qualidade do Ar')}</p>
            <p className="text-xs text-[#6a7282] mt-0.5">
              {t('history.airQualityPatternDesc', 'Atenção aos picos de CO2 nas horas de refeição.')}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
