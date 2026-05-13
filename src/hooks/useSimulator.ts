import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export function useSimulator(enabled: boolean) {
  const [eventos, setEventos] = useState<any[]>([])
  const [estadoAtual, setEstadoAtual] = useState<Record<string, number>>({})
  const [ativo, setAtivo] = useState(false)

  useEffect(() => {
    if (!enabled) return  // ← só liga quando o drawer abre

    const source = new EventSource(`${API_URL}/api/debug/simulate`)
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
  }, [enabled])  // ← re-corre quando enabled muda

  return { eventos, estadoAtual, ativo }
}