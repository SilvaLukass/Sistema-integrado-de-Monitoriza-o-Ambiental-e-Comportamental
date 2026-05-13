import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './i18n'
import './index.css'
import Layout from './components/Layout'
import { OverviewPage } from './pages/OverviewPage'
import AlertsPage from './pages/AlertsPage'
import {HistoryPage} from './pages/HistoryPage'
import { DeviceStatusPage } from './pages/DeviceStatusPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10_000,
      refetchInterval: 15_000,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<OverviewPage />} />
            <Route path="historico" element={<HistoryPage />} />
            <Route path="dispositivos" element={<DeviceStatusPage />} />
            <Route path="alertas" element={<AlertsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>
)