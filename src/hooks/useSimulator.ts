import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export function useSimulator(enabled: boolean, horaInicio?: number) {
  const [eventos, setEventos] = useState<any[]>([])
  const [estadoAtual, setEstadoAtual] = useState<Record<string, number>>({})
  const [ativo, setAtivo] = useState(false)

  useEffect(() => {
    if (!enabled) return  // ← só liga quando o drawer abre

    const url = horaInicio !== undefined
      ? `${API_URL}/api/debug/simulate?hora_inicio=${horaInicio}`
      : `${API_URL}/api/debug/simulate`
    const source = new EventSource(url)
    setAtivo(true)

    source.onmessage = (e) => {
      const evento = JSON.parse(e.data)
      setEstadoAtual(evento.state_snapshot)
      setEventos((prev) => [evento, ...prev].slice(0, 100))
    }

    source.onerror = () => {
      source.close()
      setAtivo(false)
    }

    return () => {
      source.close()
      setAtivo(false)
    }
  }, [enabled, horaInicio])  

  return { eventos, estadoAtual, ativo }
}