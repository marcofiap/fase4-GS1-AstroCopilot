import { useEffect, useRef, useState } from 'react'
import { WS_URL } from '../api'

// Conecta ao WebSocket /ws/telemetry do backend e mantém o histórico recente.
export function useTelemetry(maxPoints = 30) {
  const [latest, setLatest] = useState(null)
  const [history, setHistory] = useState([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/telemetry`)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)
    ws.onmessage = (e) => {
      const d = JSON.parse(e.data)
      const point = { ...d, time: new Date(d.ts).toLocaleTimeString() }
      setLatest(point)
      setHistory((prev) => [...prev.slice(-(maxPoints - 1)), point])
    }

    return () => ws.close()
  }, [maxPoints])

  return { latest, history, connected }
}
