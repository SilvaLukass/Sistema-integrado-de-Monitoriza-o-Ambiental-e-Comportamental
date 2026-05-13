import { useTranslation } from 'react-i18next'
import { Wind } from 'lucide-react'

interface AirQualityGaugeProps {
  score: number
  simulated?: boolean
}

//construção da circunferência
const RADIUS = 70
const CIRCUMFERENCE = 2 * Math.PI * RADIUS
const SEMICIRCLE = CIRCUMFERENCE / 2
const MAX_SCORE = 200

function scoreToOffset(score: number): number {
  const percentage = Math.min(score / MAX_SCORE, 1)
  return SEMICIRCLE - percentage * SEMICIRCLE
}


export function AirQualityGauge({ score, simulated = false }: AirQualityGaugeProps) {
  const { t } = useTranslation()

  //niveis do IQA, cores e descrição
  const iqaLevels = [
    { max: 50,  label: t('airQuality.good'),     color: '#10b981', bg: 'bg-[#f0fdf4]', text: 'text-[#10b981]', description: t('airQuality.goodDesc') },
    { max: 100, label: t('airQuality.moderate'),  color: '#f59e0b', bg: 'bg-[#fffbeb]', text: 'text-[#f59e0b]', description: t('airQuality.moderateDesc') },
    { max: 999, label: t('airQuality.bad'),       color: '#ef4444', bg: 'bg-[#fff1f2]', text: 'text-[#ef4444]', description: t('airQuality.badDesc') },
  ]

  const scaleItems = [
    { range: '0–50',   label: t('airQuality.good'),     color: '#10b981' },
    { range: '51–100', label: t('airQuality.moderate'),  color: '#f59e0b' },
    { range: '101+',   label: t('airQuality.bad'),       color: '#ef4444' },
  ]

  const level = iqaLevels.find(l => score <= l.max) ?? iqaLevels[iqaLevels.length - 1]
  const offset = scoreToOffset(score)

  // O SVG tem viewBox centrado em 90,90 (centro do círculo)
  // Os círculos são desenhados com cx=90, cy=90
  // Rodamos -90° para o arco começar à esquerda e terminar à direita

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-4">
      <div className="flex items-start gap-3">
        <div className="size-10 bg-[#f0fdf4] rounded-[14px] flex items-center justify-center shrink-0 mt-1">
          <Wind size={20} className="text-[#10b981]" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <p className="font-semibold text-lg text-[#101828]">{t('airQuality.title')}</p>
            {simulated && <span className="rounded-full bg-violet-50 px-2 py-0.5 text-xs font-semibold text-violet-700">Simulado</span>}
          </div>
          <p className="text-sm text-[#6a7282]">{t('airQuality.subtitle')}</p>
        </div>
      </div>

      <div className="flex justify-center">
        {/* 180 - largura; 110 - altura */}
        <svg viewBox="0 0 180 110" className="w-full max-w-[200px]">
          <circle
            cx="90"
            cy="90"
            r={RADIUS}
            fill="none"
            stroke="#f3f4f6"
            strokeWidth="14"
            strokeLinecap="round"
            // strokeDasharray: [arco visível, espaço]
            // Mostramos exatamente metade da circunferência como trilho
            strokeDasharray={`${SEMICIRCLE} ${CIRCUMFERENCE}`}
            transform="rotate(180, 90, 90)"
          />

          {/* Arco de progresso — a cor muda consoante o nível */}
          <circle
            cx="90"
            cy="90"
            r={RADIUS}
            fill="none"
            stroke={level.color}
            strokeWidth="14"
            strokeLinecap="round"
            strokeDasharray={`${SEMICIRCLE} ${CIRCUMFERENCE}`}
            strokeDashoffset={offset}
            transform="rotate(180, 90, 90)"
            style={{ transition: 'stroke-dashoffset 0.6s ease, stroke 0.3s ease' }}
          />

          <text
            x="90"
            y="82"
            textAnchor="middle"
            fontSize="32"
            fontWeight="700"
            fill="#101828"
            fontFamily="Inter, sans-serif"
          >
            {score}
          </text>

          <text
            x="90"
            y="100"
            textAnchor="middle"
            fontSize="11"
            fill="#6a7282"
            fontFamily="Inter, sans-serif"
          >
            {t('airQuality.score')}
          </text>
        </svg>
      </div>

      <div className={`${level.bg} rounded-[14px] px-4 py-3 flex items-center justify-between`}>
        <p className={`font-semibold text-base ${level.text}`}>{level.label}</p>
        <p className="text-sm text-[#4a5565] ml-4">{level.description}</p>
      </div>

      <div className="pt-2 border-t border-[#e5e7eb]">
        <p className="text-xs text-[#6a7282] mb-3">{t('airQuality.scaleReference')}</p>
        <div className="flex flex-col gap-2">
          {scaleItems.map((item) => (
            <div key={item.range} className="flex items-center gap-2">
              <div
                className="size-3 rounded-sm shrink-0"
                style={{ backgroundColor: item.color }}
              />
              <p className="text-xs text-[#4a5565]">
                <span className="font-medium">{item.range}</span>: {item.label}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
