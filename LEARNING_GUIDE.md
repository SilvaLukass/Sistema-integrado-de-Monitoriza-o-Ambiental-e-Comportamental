# ElderCare Full Learning Guide

This document is your "single source of truth" for the stack, architecture decisions, and practical learning path used in this project.

## 1) Project Architecture at a Glance

Current system:

- Frontend: React + TypeScript + Vite
- Backend: FastAPI (Python)
- Notifications: Telegram via `python-telegram-bot`
- Data for alerts: in-memory storage (for now)

High-level flow:

1. Frontend sends/reads alerts from backend (`/api/alerts`)
2. Backend validates request with Pydantic
3. Backend stores alert in memory
4. Backend tries to send Telegram notification
5. Backend responds with alert + notification status

Key policy in this project:

- **Best-effort notification**: alert creation succeeds even if Telegram fails.

---

## 2) Frontend Stack Explained

### React

React is the UI library used to build component-based interfaces.

- Components are functions returning JSX
- State changes trigger re-renders
- You compose pages from reusable UI blocks

Why it fits this project:

- Dashboard-style UI with reusable cards
- Easy split between view components and data hooks

### TypeScript

TypeScript adds static types on top of JavaScript.

Benefits:

- Catch errors before runtime
- Better autocompletion and refactoring
- Shared contracts between frontend and backend DTOs

In this project:

- Alert domain shape is typed in `src/types/index.ts`
- API functions return typed promises

### Vite

Vite is the dev/build tool.

- Very fast local dev server (HMR)
- Simple setup for React + TS
- Environment vars with `import.meta.env`

---

## 3) State Management: React Query vs Zustand

This is crucial.

### React Query (`@tanstack/react-query`)

Use React Query for **server state**:

- Data that comes from APIs
- Has loading/error states
- Needs caching, stale/refetch logic

In this project:

- Alerts fetched with query key `['alerts']`
- Creating an alert uses mutation + `invalidateQueries(['alerts'])`
- This keeps Overview and Alerts pages synchronized

### Zustand

Zustand is a lightweight global store for **client/UI state**.

Use it for:

- UI toggles, local preferences, wizard step, sidebar state
- Data not owned by backend

Important mental model:

- **Server state -> React Query**
- **UI/app local state -> Zustand**

If you put server data in Zustand manually, you lose automatic cache lifecycle, stale handling, and refetch logic that React Query already solves.

---

## 4) Backend Stack Explained

### FastAPI

FastAPI is an async Python web framework.

What you get:

- Fast routing and validation
- Pydantic-based request/response models
- Great DX and automatic docs

### Pydantic Models

Pydantic validates and parses data at API boundaries.

In this project:

- `AlertCreate` validates incoming alert payload
- `Alert` is the canonical stored/returned alert
- `AlertCreateResult` makes success/failure of Telegram explicit

### Lifespan + `app.state`

You initialize shared services once at startup:

- Telegram notifier
- Alert store

Why:

- Avoid recreating objects on every request
- Centralized lifecycle
- Cleaner endpoints

Pattern:

1. Build service in lifespan startup
2. Save in `app.state`
3. Access in endpoints through `request.app.state`

---

## 5) Alerts Domain Decisions

### Timestamp strategy

- Backend stores ISO timestamp (machine-friendly)
- UI/Telegram formats human-readable PT-PT string

Why:

- ISO is sortable, precise, and language-independent
- Human formatting belongs to presentation layers

### Notification policy

Current policy:

- Store alert first
- Try Telegram send
- Return:
  - `notification_sent: true` or `false`
  - `notification_error` when needed

Why:

- Avoid losing critical alerts due to temporary channel failures

---

## 6) Telegram Integration Essentials

You need:

- Bot token from BotFather
- Chat ID for recipient

Message sending path:

1. Endpoint creates alert
2. Router calls notifier service
3. Notifier uses Telegram Bot API

Common operational pitfalls:

- Wrong token/chat ID
- Bot not started by recipient (`/start`)
- Network issues/rate limits

---

## 7) CORS Explained (and why curl worked)

CORS is browser security, not backend transport.

- Browser enforces CORS headers
- `curl` does not

So you can see:

- `curl` works
- browser fetch fails

Fix in FastAPI:

- Add `CORSMiddleware`
- Allow your frontend origin (`http://localhost:5173`)

---

## 8) Python Version Caveat You Hit

You are using Python 3.9.

Important typing note:

- `str | None` is Python 3.10+ style
- In 3.9 use `Optional[str]`

Why this matters:

- Type annotation errors can crash app import before server starts

Debug rule:

- Read traceback from first app file in stack to locate root cause quickly

---

## 9) Practical API Testing Checklist

Always test these for each endpoint:

1. Happy path (valid payload)
2. Validation errors (missing/invalid fields -> 422)
3. External dependency failure (Telegram down/token invalid)
4. Browser integration (CORS/preflight)

For alerts:

- POST valid alert -> returns alert + notification status
- GET alerts -> includes newly created alert

---

## 10) Suggested Next Technical Steps

Near term:

1. Add API key auth for `POST /api/alerts`
2. Move in-memory alert store to SQLite/PostgreSQL
3. Add logging structure (request id, error context)
4. Add tests (unit + API integration)
5. Normalize response envelopes if needed

After that:

1. Add WebSocket push for real-time alerts
2. Integrate Raspberry Pi sensor ingestion route
3. Plug Isolation Forest inference service
4. Add alert rules/severity mapping strategy

---

## 11) Learning Strategy (How to Improve Faster)

You said you want to understand every line and code better alone. Use this process:

1. Build in small vertical slices (one endpoint + one UI use case)
2. Never paste code without explaining each unknown line
3. For every feature, write:
   - what problem it solves
   - where state lives
   - what can fail
4. Break things intentionally and observe behavior
5. Keep a "decision log" with why each architecture choice was made

This turns coding from "copying syntax" into systems thinking.

---

## 12) Glossary (Quick)

- **Server state**: backend-owned data (use React Query)
- **Client/UI state**: frontend-owned UI state (use Zustand)
- **DTO**: data transfer object used in API boundaries
- **Lifespan**: FastAPI startup/shutdown lifecycle hook
- **CORS**: browser policy controlling cross-origin requests
- **Best-effort**: try operation, do not fail core flow if it fails

---

## 13) One-Page Mental Model

If you remember only this:

- Validate at boundaries (Pydantic)
- Keep endpoints thin, logic in services
- Initialize integrations once at startup
- Keep server state in React Query
- Keep UI state in Zustand
- Persist important data before optional side effects
- Make failures explicit in responses

