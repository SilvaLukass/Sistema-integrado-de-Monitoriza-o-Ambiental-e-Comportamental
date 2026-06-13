# ElderCare — Plataforma IoT de Monitorização para a Terceira Idade

Dashboard de monitorização não invasiva de idosos, desenvolvido como projeto final de Licenciatura em Engenharia Informática na UTAD.

O sistema prevê integração de sensores ambientais e comportamentais (PIR, reed switch, DHT22, MQ2, Grove Air Quality) num Raspberry Pi, com agregação e visualização dos dados num dashboard web. A arquitetura de referência no **branch `main`** prevê **Home Assistant** como camada de agregação (MQTT → HA → API). No **desenvolvimento atual** (ver secção abaixo) existe também um **backend FastAPI** em Python para alertas e notificações (Telegram), com dados ainda maioritariamente simulados no frontend até haver hardware.

---

## Stack

| Camada | Tecnologia | Motivo |
|--------|------------|--------|
| UI | React 19 + TypeScript | Tipagem estática, ecossistema maduro |
| Build | Vite | HMR rápido, build simples |
| Estilos | Tailwind CSS v4 | Utility-first, pouco CSS manual |
| Routing | React Router 7 | Nested routes, layout com `<Outlet />` |
| Estado local / preferências | Zustand | Leve; exemplo: modo simples na UI (persistido em `localStorage`) |
| Dados do servidor | TanStack Query | Cache, refetch, estados de loading/erro |
| Gráficos | Recharts | Declarativo, integração natural com React |
| i18n | i18next + react-i18next | PT/EN via `src/locales/` |
| Backend (atual) | FastAPI + Uvicorn | API REST, validação com Pydantic, async |
| Notificações (atual) | Telegram (`python-telegram-bot`) | Alertas para tutor/cuidador no telemóvel |

---

## Estrutura do repositório

```
src/
├── api/
│   ├── backend.ts             # Cliente HTTP para API FastAPI (alertas)
│   └── homeAssistant.ts       # Cliente REST + WebSocket Home Assistant (preparado; integração opcional)
├── components/
│   ├── Layout.tsx
│   ├── Sidebar.tsx            # Navegação + idioma + modo simples
│   ├── AirQualityGauge.tsx
│   └── OccupancyHeatmap.tsx
├── locales/
│   ├── pt/translation.json
│   └── en/translation.json
├── pages/
│   ├── OverviewPage.tsx
│   ├── HistoryPage.tsx
│   ├── DeviceStatusPage.tsx
│   └── AlertsPage.tsx
├── store/
│   └── appStore.ts            # Zustand (ex.: simpleMode persistido)
├── types/
│   └── index.ts
├── i18n.ts
└── main.tsx                   # Entry: QueryClient, Router, rotas

backend/
├── app/
│   ├── main.py                # FastAPI, CORS, lifespan, serviços em app.state
│   ├── config.py              # Settings (env)
│   ├── models.py              # Modelos Pydantic
│   ├── routers/
│   │   └── alerts.py          # GET/POST /api/alerts
│   └── services/
│       ├── alert_store.py     # Armazenamento em memória (protótipo)
│       └── telegram_notifier.py
└── .env                       # Não commitar segredos — ver abaixo

LEARNING_GUIDE.md              # (raiz) decisões de arquitetura e aprendizagem
```

### Dependências Python (backend)

Criar venv e instalar (exemplo):

```bash
pip install fastapi "uvicorn[standard]" python-telegram-bot pydantic-settings
```

Recomenda-se adicionar um `requirements.txt` no repositório para reprodutibilidade.

---

## Correr localmente

### Frontend

```bash
npm install
npm run dev
```

Por defeito o Vite usa `http://localhost:5173` (se a porta estiver ocupada, pode usar 5174 — nesse caso o backend tem de aceitar essa origem em CORS).

### Backend (FastAPI)

Na pasta do backend, com ambiente Python ativo e dependências instaladas:

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

- Health check: `GET http://127.0.0.1:8000/health`
- Alertas: `GET/POST http://127.0.0.1:8000/api/alerts`

Se correres o `uvicorn` a partir da **raiz** do repositório, o módulo da app pode ser referenciado como `backend.app.main:app` (ajusta conforme o teu `cwd`).

### Variáveis de ambiente

**Raiz do projeto (frontend)** — opcional:

| Variável | Descrição |
|----------|-----------|
| `VITE_API_URL` | URL do FastAPI (ex.: `http://localhost:8000`). Se omitida, o cliente usa `http://localhost:8000`. |
| `VITE_HA_URL` | URL do Home Assistant (quando a integração HA estiver ativa no cliente). |
| `VITE_HA_TOKEN` | Token de longa duração do Home Assistant. |

**Backend** — ficheiro `backend/.env` (não commitar tokens):

| Variável | Descrição |
|----------|-----------|
| `TELEGRAM_BOT_TOKEN` | Token do bot (BotFather) |
| `TELEGRAM_CHAT_ID` | ID do chat para envio de mensagens |
| `CORS_ORIGINS` | Origens permitidas, separadas por vírgula (ex.: `http://localhost:5173,http://localhost:5174`) |
| `SIMULATOR_ENABLED` | `false` por defeito. Usa dados sintéticos no PC; mete `true` só para demo sem Raspberry Pi |
| `CONSUMER_ENABLED` | `true` para o backend consumir leituras do RabbitMQ (RPi ou simulador) |

---

## Arquitetura (visão geral)

### Referência académica (edge + HA)

```
Sensores → Raspberry Pi → Broker MQTT → Home Assistant → API REST/WebSocket → Dashboard React
                                                              ↕
                                              Isolation Forest (ML) — em desenvolvimento
```

### Estado atual do desenvolvimento

Além do dashboard, existe um **serviço FastAPI** que:

- expõe **alertas** (`/api/alerts`);
- tenta enviar **notificações Telegram** com política *best-effort* (o alerta regista-se mesmo que o Telegram falhe);
- usa **CORS** para o browser (`localhost` com portas do Vite).

O cliente `src/api/homeAssistant.ts` mantém a **linha de evolução** para consumir o Home Assistant quando a integração estiver completa no frontend.

---

## Estado deste branch (desenvolvimento)

Esta secção documenta o que está **implementado além do `main` genérico** ou em paralelo com a visão “só Home Assistant”.

### Implementado

- **Backend FastAPI**: modelo de alertas com Pydantic, armazenamento em memória, `GET`/`POST /api/alerts`, notificações Telegram, endpoint de teste de notificação, middleware **CORS** configurável.
- **Frontend ligado ao backend**: página de alertas e cartões de alertas na visão geral consomem a API real (TanStack Query).
- **Modo simples (UI)**: preferência global (`simpleMode`) no Zustand com **persistência** em `localStorage`; alternância na sidebar; em modo simples, cartões de dispositivos mostram sobretudo **online/offline**; alinhamento de nome + estado nas vistas relevantes.
- **Internacionalização**: strings em PT/EN; chaves para modo simples e restantes vistas.
- **Documentação de aprendizagem**: `LEARNING_GUIDE.md` na raiz com decisões de arquitetura (React Query vs Zustand, CORS, política de notificações, etc.).

### Em mock / por integrar

- **Dados de sensores, histórico, métricas do RPi**: grande parte das páginas (ex.: histórico, alguns cartões na visão geral) ainda usa **dados simulados** até existir Raspberry Pi e pipeline estável.
- **Home Assistant no browser**: cliente preparado; substituição progressiva dos mocks por `fetch`/WebSocket conforme a equipa fechar a camada HA.
- **Isolation Forest**: desenvolvimento em paralelo (outro branch); integração futura como serviço que alimenta criação de alertas ou scores.
- **Persistência de alertas**: atualmente em memória no processo Python (reinício = perda); evolução natural: SQLite ou outra BD.
- **Autenticação**: não incluída; para produção ou exposição em rede, considerar API keys ou login.

---

## Internacionalização

As strings estão em `src/locales/{lang}/translation.json`. A língua por defeito é **português**. Para novo idioma: duplicar chaves noutro ficheiro e registar em `src/i18n.ts`.

---

## Contexto académico

**Projeto Final de Licenciatura** — Engenharia Informática, UTAD

**Título:** *Plataforma IoT Multimodal para a Terceira Idade: Integração de Monitorização Ambiental e Comportamental*

---

## Licença e autores

(Ajustar conforme a equipa e a política da UTAD.)
