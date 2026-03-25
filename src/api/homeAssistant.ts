const HA_URL = import.meta.env.VITE_HA_URL ?? 'http://homeassistant.local:8123'
const HA_TOKEN = import.meta.env.VITE_HA_TOKEN ?? ''

const headers = {
  'Content-Type': 'application/json',
  Authorization: `Bearer ${HA_TOKEN}`,
}

export async function fetchEntityState(entityId: string) {
  const res = await fetch(`${HA_URL}/api/states/${entityId}`, { headers })
  if (!res.ok) throw new Error(`Erro ao buscar ${entityId}: ${res.status}`)
  return res.json()
}

export async function fetchAllStates() {
  const res = await fetch(`${HA_URL}/api/states`, { headers })
  if (!res.ok) throw new Error(`Erro ao buscar estados: ${res.status}`)
  return res.json()
}

// Subscreve a eventos em tempo real via WebSocket
// onMessage é chamado sempre que chega um novo evento do HA
export function subscribeToHA(onMessage: (data: unknown) => void): WebSocket {
  const ws = new WebSocket(`${HA_URL.replace('http', 'ws')}/api/websocket`)

  ws.onopen = () => {
    ws.send(JSON.stringify({ type: 'auth', access_token: HA_TOKEN }))
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.type === 'auth_ok') {
      ws.send(JSON.stringify({ id: 1, type: 'subscribe_events', event_type: 'state_changed' }))
    }

    if (data.type === 'event') {
      onMessage(data.event)
    }
  }

  return ws
}