import { useState } from 'react'
import {
    Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Line, ComposedChart, Legend
} from 'recharts'
import { Activity, Flame } from 'lucide-react'
import { useTranslation } from 'react-i18next'

// Simulamos 24 horas de dados complexos
const mockComplexData = Array.from({ length: 24 }, (_, i) => {
    // Picos de movimento (manhã e fim de tarde)
    let movement = 0
    if (i > 7 && i < 11) movement = 60 + Math.random() * 30
    if (i >= 11 && i < 17) movement = 20 + Math.random() * 20
    if (i >= 17 && i < 22) movement = 50 + Math.random() * 40

    // Temperatura/Humidade estabiliza, mas sobe nas horas quentes e à noite (aquecimento)
    let tempHum = 40 + (Math.sin((i - 6) * (Math.PI / 12)) * 15) + Math.random() * 5

    // Picos de CO2/Gás apenas nas horas de refeição (Cozinha)
    let co2 = 400 + Math.random() * 50
    if (i === 13 || i === 14) co2 = 800 + Math.random() * 300 // Almoço
    if (i === 19 || i === 20) co2 = 1200 + Math.random() * 400 // Jantar longo

    return {
        time: `${String(i).padStart(2, '0')}:00`,
        movement: Math.round(movement),
        tempHum: Math.round(tempHum),
        co2: Math.round(co2)
    }
})

export function AdvancedHistoryChart() {
    const { t } = useTranslation()
    const [activeMetric, setActiveMetric] = useState('all')

    // --- LÓGICA DE TRADUÇÃO (Dentro do componente para aceder ao 't') ---
    const getCO2Status = (ppm: number) => {
        if (ppm <= 800) return t('airQuality.good', 'Bom');
        if (ppm <= 1200) return t('airQuality.moderate', 'Atenção');
        return t('airQuality.bad', 'Mau/Perigoso');
    }

    return (
        <div className="bg-white border border-[#e5e7eb] rounded-[14px] shadow-sm p-6 flex flex-col gap-6">

            {/* Cabeçalho Interativo */}
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
                        className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${activeMetric === 'all' ? 'bg-white shadow-sm text-[#101828]' : 'text-[#6a7282]'}`}
                    >
                        {t('history.overview', 'Visão Geral')}
                    </button>
                    <button
                        onClick={() => setActiveMetric('co2')}
                        className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1 ${activeMetric === 'co2' ? 'bg-white shadow-sm text-[#ef4444]' : 'text-[#6a7282]'}`}
                    >
                        <Flame size={14} /> {t('sensors.gas', 'Gás / CO2')}
                    </button>
                </div>
            </div>

            {/* Área do Gráfico */}
            <div className="h-[350px] w-full mt-4">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={mockComplexData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                        <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6a7282' }} dy={10} />

                        <YAxis yAxisId="left" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6a7282' }} />

                        <YAxis
                            yAxisId="right"
                            orientation="right"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fontSize: 12, fill: '#ef4444', fontWeight: 600 }}
                            domain={[400, 2000]}
                            ticks={[400, 1000, 1600]}
                            tickFormatter={(value: any) => getCO2Status(Number(value))}
                        />

                        <Tooltip
                            formatter={(value: any, name: any) => {
                                const numericValue = Number(value);
                                // Verificamos o nome traduzido ou a chave original
                                if (name === t('sensors.co2Level', "Níveis de CO2 (ppm)")) {
                                    return [`${numericValue} ppm (${getCO2Status(numericValue)})`, t('sensors.airQuality', "Qualidade do Ar")];
                                }
                                if (name === t('history.routineActivity', "Atividade (Rotina)")) {
                                    return [`${numericValue}%`, name];
                                }
                                return [numericValue, name];
                            }}
                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                            labelStyle={{ fontWeight: 'bold', color: '#101828', marginBottom: '4px' }}
                        />
                        <Legend wrapperStyle={{ paddingTop: '20px' }} />

                        {(activeMetric === 'all' || activeMetric === 'movement') && (
                            <Area
                                yAxisId="left"
                                type="monotone"
                                dataKey="movement"
                                name={t('history.routineActivity', "Atividade (Rotina)")}
                                stroke="#3b82f6"
                                fill="#eff6ff"
                                strokeWidth={2}
                            />
                        )}

                        {(activeMetric === 'all' || activeMetric === 'temp') && (
                            <Line
                                yAxisId="left"
                                type="monotone"
                                dataKey="tempHum"
                                name={t('sensors.temperature', "Temp / Humidade")}
                                stroke="#f59e0b"
                                strokeWidth={2}
                                dot={false}
                            />
                        )}

                        {(activeMetric === 'all' || activeMetric === 'co2') && (
                            <Line
                                yAxisId="right"
                                type="monotone"
                                dataKey="co2"
                                name={t('sensors.co2Level', "Níveis de CO2 (ppm)")}
                                stroke="#ef4444"
                                strokeWidth={2}
                                dot={{ r: 3, fill: '#ef4444' }}
                                activeDot={{ r: 6 }}
                            />
                        )}
                    </ComposedChart>
                </ResponsiveContainer>
            </div>

            {/* Interpretação Automática (Rodapé) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-[#e5e7eb]">
                {/* Repetir a lógica de tradução para as 3 colunas como já estavas a fazer */}
                <div className="flex gap-3 items-start">
                    <div className="mt-1 size-8 rounded-full bg-[#eff6ff] flex items-center justify-center shrink-0">
                        <Activity size={16} className="text-[#3b82f6]" />
                    </div>
                    <div>
                        <p className="text-sm font-semibold text-[#101828]">{t('history.sleepPatternTitle', 'Padrão de Sono')}</p>
                        <p className="text-xs text-[#6a7282] mt-0.5">{t('history.sleepPatternDesc', 'Atividade mínima...')}</p>
                    </div>
                </div>
                {/* ... (as outras duas colunas seguem o mesmo padrão) */}
            </div>
        </div>
    )
}