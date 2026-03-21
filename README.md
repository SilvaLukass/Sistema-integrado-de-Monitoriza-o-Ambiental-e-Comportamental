# ElderCare — Plataforma IoT de Monitorização para a Terceira Idade

Dashboard de monitorização não invasiva de idosos, desenvolvido como projeto final de Licenciatura em Engenharia Informática na UTAD.

O sistema integra sensores ambientais e comportamentais (PIR, reed switch, DHT22, MQ2, Grove Air Quality) controlados por um Raspberry Pi, comunicando via MQTT com o Home Assistant como camada de agregação de dados. Este repositório contém o dashboard React que consome a API do Home Assistant.

---

## Stack

| Camada | Tecnologia | Motivo |
|---|---|---|
| UI | React 19 + TypeScript | Tipagem estática, ecossistema maduro |
| Build | Vite | HMR instantâneo, build rápido |
| Estilos | Tailwind CSS v4 | Utility-first, sem CSS files |
| Routing | React Router v6 | Nested routing, layout pattern |
| Estado global | Zustand | Simples, sem boilerplate |
| Data fetching | TanStack Query | Cache, polling automático, loading states |
| Gráficos | Recharts | Declarativo, nativo React |
| i18n | i18next + react-i18next | Suporte PT/EN via ficheiros JSON |

---

## Estrutura do Projeto
```
src/
├── api/
│   └── homeAssistant.ts      # Cliente REST + WebSocket do Home Assistant
├── components/
│   ├── Layout.tsx             # Layout com Sidebar + Outlet
│   ├── Sidebar.tsx            # Navegação lateral
│   ├── AirQualityGauge.tsx    # Gauge IQA em SVG puro
│   └── OccupancyHeatmap.tsx   # Heatmap semanal em CSS Grid
├── locales/
│   ├── pt/translation.json    # Strings em português
│   └── en/translation.json    # Strings em inglês
├── pages/
│   ├── OverviewPage.tsx       # Dashboard principal
│   ├── HistoryPage.tsx        # Gráficos e heatmap
│   ├── DeviceStatusPage.tsx   # Estado do RPi e sensores
│   └── AlertsPage.tsx         # Lista de alertas
├── store/
│   └── appStore.ts            # Estado global (Zustand)
├── types/
│   └── index.ts               # Tipos TypeScript do domínio
├── i18n.ts                    # Configuração i18next
└── main.tsx                   # Entry point, providers, rotas
```

---

## Correr Localmente
```bash
# Instalar dependências
npm install

# Desenvolvimento
npm run dev

# Build de produção
npm run build
```

---

## Variáveis de Ambiente

Cria um ficheiro `.env` na raiz com:
```env
VITE_HA_URL=http://homeassistant.local:8123
VITE_HA_TOKEN=<long-lived-access-token>
```

O token é gerado no Home Assistant em **Perfil → Tokens de acesso de longa duração**.

Sem estas variáveis, o dashboard corre com mock data e não tenta ligar ao Home Assistant.

---

## Estado Atual

**Implementado**
- [x] Estrutura completa do projeto (routing, i18n, estado global, cliente HA)
- [x] Overview — safety status, timeline de atividade, saúde ambiental, alertas recentes, estado de dispositivos
- [x] History — gráfico de área (Recharts), gauge IQA (SVG), heatmap semanal (CSS Grid)
- [x] Device Status — métricas do RPi, cards de sensores, lista de dispositivos
- [x] Alerts — lista com níveis de severidade

**Por fazer**
- [ ] Integração real com a API do Home Assistant (substituir mock data)
- [ ] Ligação WebSocket para atualizações em tempo real
- [ ] Autenticação / página de login
- [ ] Integração com modelo de ML (Isolation Forest) para alertas de anomalia

---

## Internacionalização

As strings da aplicação estão em `src/locales/{lang}/translation.json`. A língua por defeito é português (`pt`). Para adicionar um idioma novo:

1. Cria `src/locales/{lang}/translation.json` com as mesmas chaves
2. Regista o novo idioma em `src/i18n.ts`

---

## Arquitetura do Sistema
```
Sensores → Raspberry Pi → Broker MQTT (Mosquitto) → Home Assistant → API REST/WebSocket → Dashboard React
                                                            ↕
                                                   Isolation Forest (ML)
```

O Home Assistant agrega os dados dos sensores, persiste o histórico e expõe uma API que o dashboard consome. O processamento corre localmente (edge computing), sem dependência de serviços cloud.

---

## Contexto Académico

Projeto Final de Licenciatura — Engenharia Informática, UTAD  
Título: *Plataforma IoT Multimodal para a Terceira Idade: Integração de Monitorização Ambiental e Comportamental*
