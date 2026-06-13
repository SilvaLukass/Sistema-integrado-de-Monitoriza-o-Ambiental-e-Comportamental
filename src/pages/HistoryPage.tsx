import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { ActivityTrendsChart } from '../components/ActivityTrendsChart'
import { AirQualityGauge } from '../components/AirQualityGauge'
import { OccupancyHeatmap } from '../components/OccupancyHeatmap'
import { getLatestSensors } from '../api/backend'

function co2ToAirQualityScore(co2: number): number {
  // The gauge is an air-quality index, not raw ppm: 400 ppm is excellent,
  // 1600 ppm is very poor, and values are clamped to the 0-200 gauge range.
  return Math.round(Math.min(Math.max(((co2 - 400) / 1200) * 200, 0), 200))
}

export function HistoryPage() {
  const { t } = useTranslation()
  const { data: latestSensors } = useQuery({
    queryKey: ['latest-sensors'],
    queryFn: getLatestSensors,
    refetchInterval: 30_000,
    retry: false,
  })
  const airQualityScore = co2ToAirQualityScore(latestSensors?.co2 ?? 400)

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-[#101828]">{t('history.title')}</h1>
        <p className="text-sm text-[#6a7282] mt-1">{t('history.subtitle')}</p>
      </div>

      <div className="grid grid-cols-[3fr_1fr] gap-6">
        <ActivityTrendsChart />
        <AirQualityGauge score={airQualityScore} simulated />
      </div>

      <OccupancyHeatmap />

    </div>
  )
}
