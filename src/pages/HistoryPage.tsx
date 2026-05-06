import { useTranslation } from 'react-i18next'
import { AirQualityGauge } from '../components/AirQualityGauge'
import { OccupancyHeatmap } from '../components/OccupancyHeatmap'
export function HistoryPage() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-[#101828]">{t('history.title')}</h1>
        <p className="text-sm text-[#6a7282] mt-1">{t('history.subtitle')}</p>
      </div>

      <div className="grid grid-cols-[3fr_1fr] gap-6">
        {/* <ActivityTrendsChart /> */}
        <AirQualityGauge score={100} />
      </div>

      <OccupancyHeatmap />

    </div>
  )
}
